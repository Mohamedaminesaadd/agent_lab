"""
Architecture multi-agents LangGraph : superviseur + 3 spécialistes (hôtel, vol, RH).

Topologie du graphe :

    START -> supervisor -> (hotel_agent | flight_agent | hr_agent | END)

    hotel_agent  -> hotel_tools  -> hotel_agent  -> supervisor
    flight_agent -> flight_tools -> flight_agent -> supervisor
    hr_agent     -> hr_tools     -> hr_agent     -> supervisor

Chaque agent = base_llm + prompt système dédié + sous-ensemble d'outils.
Le superviseur ne répond jamais à l'utilisateur : il ne fait que router.
"""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# --------------------------------------------------------------------------- #
# 1. État partagé
# --------------------------------------------------------------------------- #

class GraphState(TypedDict):
    # Historique de conversation (reducer add_messages = append + dédup par id)
    messages: Annotated[list, add_messages]

    # Décision du superviseur, lue par la fonction de routage
    next_agent: str

    # Informations métier partagées entre agents
    hotel: str
    flight_reserved: bool
    vacation_requested: bool

    # Garde-fou anti-boucle infinie (le superviseur peut re-router indéfiniment)
    steps: int


MAX_STEPS = 10


# --------------------------------------------------------------------------- #
# 2. Outils
# --------------------------------------------------------------------------- #
# Règle : un outil DOIT retourner une string (ou un objet sérialisable).
# Les versions dupliquées de ton fichier (serachHotel, reservation_airplane)
# ne retournaient rien -> le ToolMessage aurait été vide.

HOTELS = {
    "Tunisia": ["Golden Tulip", "Movenpick Sousse", "Iberostar Selection"],
    "Spain": ["Hotel Ritz Madrid", "Barcelona Princess", "Gran Hotel Bali"],
    "France": ["Le Meurice", "Hotel Lutetia", "Shangri-La Paris"],
}


@tool
def search_hotel(country: str) -> str:
    """Rechercher les hôtels disponibles dans un pays donné."""
    result = HOTELS.get(country)
    if result is None:
        return f"Aucun hôtel trouvé pour {country}."
    return "\n".join(result)


@tool
def reserve_airplane(destination: str) -> str:
    """Réserver un billet d'avion vers une destination."""
    return f"Vol réservé avec succès vers {destination}."


@tool
def take_vacation(days: int) -> str:
    """Notifier les RH d'une demande de congé."""
    return f"Demande de congé de {days} jour(s) envoyée aux RH."


hotel_tools = [search_hotel]
flight_tools = [reserve_airplane]
hr_tools = [take_vacation]


# --------------------------------------------------------------------------- #
# 3. LLM de base + agents (base_llm + prompt + bind_tools)
# --------------------------------------------------------------------------- #

base_llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5:14b",
    temperature=0,
)

# Le superviseur n'a AUCUN outil : il produit uniquement un mot-clé.
supervisor_llm = base_llm

hotel_llm = base_llm.bind_tools(hotel_tools)
flight_llm = base_llm.bind_tools(flight_tools)
hr_llm = base_llm.bind_tools(hr_tools)


HOTEL_PROMPT = SystemMessage(
    content="""Tu es un spécialiste de la réservation d'hôtels.

Responsabilités :
- Rechercher des hôtels via l'outil search_hotel
- Recommander un hôtel
- Répondre aux questions hôtelières

Interdictions :
- Réserver un avion
- Contacter les RH
"""
)

FLIGHT_PROMPT = SystemMessage(
    content="""Tu es un expert en réservation de vols.

Ta seule responsabilité est de réserver des billets d'avion via reserve_airplane.

Ne recommande jamais d'hôtel. Ne contacte jamais les RH.
"""
)

HR_PROMPT = SystemMessage(
    content="""Tu travailles aux Ressources Humaines.

Ta seule tâche est de notifier les RH qu'un employé part en congé via take_vacation.

Ne recherche jamais d'hôtel. Ne réserve jamais de vol.
"""
)

SUPERVISOR_PROMPT = SystemMessage(
    content="""Tu es le superviseur d'une agence de voyage.

Ton rôle n'est PAS de répondre à l'utilisateur.
Ta seule responsabilité est de décider quel spécialiste doit travailler ensuite.

Spécialistes disponibles :
- hotel   : rechercher et recommander des hôtels
- flight  : réserver un billet d'avion
- hr      : notifier les RH d'un congé

Si toutes les tâches demandées sont terminées, réponds : finish

Réponds par UN SEUL mot, sans ponctuation ni explication :
hotel
flight
hr
finish
"""
)


# --------------------------------------------------------------------------- #
# 4. Nœuds
# --------------------------------------------------------------------------- #

VALID_AGENTS = {"hotel", "flight", "hr", "finish"}


def _sync_flags(state: GraphState) -> dict:
    """
    Dérive les drapeaux métier depuis les ToolMessages déjà présents.
    Évite d'avoir à muter l'état à l'intérieur des ToolNode (impossible).
    """
    flags = {
        "hotel": state.get("hotel", ""),
        "flight_reserved": state.get("flight_reserved", False),
        "vacation_requested": state.get("vacation_requested", False),
    }

    for msg in state["messages"]:
        if not isinstance(msg, ToolMessage):
            continue
        if msg.name == "search_hotel":
            flags["hotel"] = msg.content
        elif msg.name == "reserve_airplane":
            flags["flight_reserved"] = True
        elif msg.name == "take_vacation":
            flags["vacation_requested"] = True

    return flags


def supervisor(state: GraphState) -> dict:
    flags = _sync_flags(state)
    steps = state.get("steps", 0) + 1

    # Garde-fou : on coupe avant la boucle infinie
    if steps > MAX_STEPS:
        return {"next_agent": "finish", "steps": steps, **flags}

    # On donne au superviseur l'état d'avancement, sinon il re-route en boucle
    context = SystemMessage(
        content=(
            "État actuel des tâches :\n"
            f"- hôtel recherché : {'oui' if flags['hotel'] else 'non'}\n"
            f"- vol réservé : {'oui' if flags['flight_reserved'] else 'non'}\n"
            f"- congé demandé : {'oui' if flags['vacation_requested'] else 'non'}"
        )
    )

    response = supervisor_llm.invoke(
        [SUPERVISOR_PROMPT, *state["messages"], context]
    )

    # Normalisation défensive : un petit modèle local ajoute souvent du bruit
    decision = response.content.strip().lower().split()
    decision = decision[0].strip(".,:;\"'") if decision else "finish"
    if decision not in VALID_AGENTS:
        decision = "finish"

    print(f"\n===== SUPERVISOR (step {steps}) -> {decision} =====")

    # Important : on ne renvoie PAS response dans messages,
    # la décision du superviseur ne fait pas partie de la conversation.
    return {"next_agent": decision, "steps": steps, **flags}


def hotel_agent(state: GraphState) -> dict:
    response = hotel_llm.invoke([HOTEL_PROMPT, *state["messages"]])
    return {"messages": [response]}


def flight_agent(state: GraphState) -> dict:
    response = flight_llm.invoke([FLIGHT_PROMPT, *state["messages"]])
    return {"messages": [response]}


def hr_agent(state: GraphState) -> dict:
    response = hr_llm.invoke([HR_PROMPT, *state["messages"]])
    return {"messages": [response]}


# ToolNode exécute automatiquement tous les tool_calls du dernier AIMessage
hotel_tool_node = ToolNode(hotel_tools)
flight_tool_node = ToolNode(flight_tools)
hr_tool_node = ToolNode(hr_tools)


# --------------------------------------------------------------------------- #
# 5. Routage
# --------------------------------------------------------------------------- #

def route_supervisor(state: GraphState) -> Literal["hotel", "flight", "hr", "finish"]:
    return state["next_agent"]


# --------------------------------------------------------------------------- #
# 6. Construction du graphe
# --------------------------------------------------------------------------- #

graph = StateGraph(GraphState)

graph.add_node("supervisor", supervisor)

graph.add_node("hotel_agent", hotel_agent)
graph.add_node("hotel_tools", hotel_tool_node)

graph.add_node("flight_agent", flight_agent)
graph.add_node("flight_tools", flight_tool_node)

graph.add_node("hr_agent", hr_agent)
graph.add_node("hr_tools", hr_tool_node)

graph.add_edge(START, "supervisor")

# Superviseur -> spécialiste (ou fin)
graph.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "hotel": "hotel_agent",
        "flight": "flight_agent",
        "hr": "hr_agent",
        "finish": END,
    },
)

# Pour chaque agent : tools_condition renvoie "tools" ou END.
# Le path_map remappe "tools" vers le ToolNode dédié,
# et END vers le superviseur (l'agent a fini son tour).
for agent, tools_node in (
    ("hotel_agent", "hotel_tools"),
    ("flight_agent", "flight_tools"),
    ("hr_agent", "hr_tools"),
):
    graph.add_conditional_edges(
        agent,
        tools_condition,
        {"tools": tools_node, END: "supervisor"},
    )
    graph.add_edge(tools_node, agent)  # retour à l'agent pour interpréter le résultat

app = graph.compile()


# --------------------------------------------------------------------------- #
# 7. Exécution
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    initial_state: GraphState = {
        "messages": [
            (
                "user",
                "Je pars en vacances en Tunisie pendant 7 jours. "
                "Trouve-moi un hôtel, réserve le vol et préviens les RH.",
            )
        ],
        "next_agent": "",
        "hotel": "",
        "flight_reserved": False,
        "vacation_requested": False,
        "steps": 0,
    }

    final_state = app.invoke(initial_state, config={"recursion_limit": 50})

    for message in final_state["messages"]:
        message.pretty_print()