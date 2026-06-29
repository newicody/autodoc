digraph Global {
    rankdir=TB;
    compound=true;
    // Styles généraux
    node [shape=box, style=filled, fontname="Arial", fontsize=10];
    // L0 - Hardware
    subgraph cluster_L0 {
        label="Hardware Layer";
        color="#c62828"; bgcolor="#ffebee";
        node [fillcolor="#ffebee", color="#c62828"];
        CPU [label="Intel i5-11400\nCPU Affinity"];
        RAM [label="128GB DDR4"];
        Storage [label="ZFS\nNVMe stripe overlay\nRAIDZ2 SATA"];
        GPU [label="Intel iGPU\nOpenVINO Backend"];
    }
    // L1 - Micro Kernel
    subgraph cluster_L1 {
        label="MissiPy Micro Kernel";
        color="#512da8"; bgcolor="#ede7f6";
        node [fillcolor="#ede7f6", color="#512da8"];
        Launcher; Registry; Proxy; Scheduler; Dispatcher; Queue; EventBus; Policy; Lifecycle;
    }
    // L2 - Context Fabric
    subgraph cluster_L2 {
        label="Global Context Fabric";
        color="#ef6c00"; bgcolor="#fff3e0";
        node [fillcolor="#fff3e0", color="#ef6c00"];
        GET; Collector; Reducer; Snapshot; Inference; Adapter; Decision;
    }
    // L3 - Services
    subgraph cluster_L3 {
        label="Independent Services";
        color="#0288d1"; bgcolor="#e1f5fe";
        node [fillcolor="#e1f5fe", color="#0288d1"];
        SQLiteProd; SQLiteMaint; Qdrant; Cache; Knowledge; Router;
    }
    // L4 - AI Backends
    subgraph cluster_L4 {
        label="AI Backends";
        color="#fbc02d"; bgcolor="#fffde7";
        node [fillcolor="#fffde7", color="#fbc02d"];
        OpenVINO; Embedding; MCTS;
    }
    // L5 - Experts
    subgraph cluster_L5 {
        label="Expert Components";
        color="#388e3c"; bgcolor="#e8f5e9";
        node [fillcolor="#e8f5e9", color="#388e3c"];
        Meta; Python; C; KiCad; FreeCAD; Web; SVG;
    }
    // L6 - Validation
    subgraph cluster_L6 {
        label="Validation Pipeline";
        color="#7b1fa2"; bgcolor="#f3e5f5";
        node [fillcolor="#f3e5f5", color="#7b1fa2"];
        Compiler; Tests; Validator; Confidence; Conflict; Version;
    }
    // L7 - Observability
    subgraph cluster_L7 {
        label="Observability";
        color="#666666"; bgcolor="#f5f5f5";
        node [fillcolor="#f5f5f5", color="#666666"];
        Logger; Metrics; Replay; Dashboard; Watchdog;
    }

    // === Relations avec commentaires ===

    // Initialisation du noyau
    // Le Launcher déclenche la découverte des composants
    Launcher -> Registry;
    // Le registre fournit les composants au Proxy
    Registry -> Proxy;
    // Le Proxy transmet les événements au Scheduler
    Proxy -> Scheduler;
    // Le Scheduler dépose les événements dans la file prioritaire
    Scheduler -> Queue;
    // La file alimente le Dispatcher
    Queue -> Dispatcher;
    // Le Dispatcher publie sur l'Event Bus
    Dispatcher -> EventBus;

    // Boucle de contexte
    // Le Scheduler émet un tick d'horloge pour GET_CONTEXT_ALL
    Scheduler -> GET [label="Clock Tick"];
    // GET_CONTEXT_ALL interroge le Proxy pour le contexte
    GET -> Proxy [label="context()"];
    // Le Proxy envoie les données brutes au Collector
    Proxy -> Collector;
    // Le Collector transmet les données agrégées au Reducer
    Collector -> Reducer;
    // Le Reducer produit un Snapshot immuable
    Reducer -> Snapshot;
    // Le Snapshot est transformé en InferenceContext
    Snapshot -> Inference;
    // L'InferenceContext est adapté pour la décision
    Inference -> Adapter;
    // L'Adapter envoie le contexte interprété au Decision Engine
    Adapter -> Decision;

    // Décisions vers la politique et le Scheduler
    // Le Decision Engine influence la Policy
    Decision -> Policy;
    // La Policy ajuste les paramètres du Scheduler
    Policy -> Scheduler;
    // Le Decision Engine peut injecter directement dans la Queue
    Decision -> Queue [style=dashed];
    // Le Decision Engine peut lancer une exploration MCTS
    Decision -> MCTS [style=dashed];

    // Services indépendants
    // L'Event Bus alimente SQLite Production (source de vérité)
    EventBus -> SQLiteProd;
    // L'Event Bus alimente SQLite Maintenance (apprentissage)
    EventBus -> SQLiteMaint;
    // L'Event Bus alimente Qdrant (mémoire vectorielle)
    EventBus -> Qdrant;
    // L'Event Bus alimente le Cache d'inférence
    EventBus -> Cache;
    // L'Event Bus alimente le Knowledge Manager
    EventBus -> Knowledge;
    // L'Event Bus alimente le Routeur sémantique
    EventBus -> Router;

    // Backends IA
    // L'Adapter pilote le runtime OpenVINO
    Adapter -> OpenVINO;
    // L'Adapter pilote le moteur d'embeddings
    Adapter -> Embedding;
    // Qdrant fournit des vecteurs au moteur d'embeddings
    Qdrant -> Embedding;

    // Experts (via Proxy)
    // Le Proxy délègue à l'expert Meta
    Proxy -> Meta;
    // Le Proxy délègue à l'expert Python
    Proxy -> Python;
    // Le Proxy délègue à l'expert C/ASM
    Proxy -> C;
    // Le Proxy délègue à l'expert KiCad
    Proxy -> KiCad;
    // Le Proxy délègue à l'expert FreeCAD
    Proxy -> FreeCAD;
    // Le Proxy délègue à l'expert Web
    Proxy -> Web;
    // Le Proxy délègue à l'expert SVG/MIDI
    Proxy -> SVG;

    // Pipeline de validation
    // Le Proxy soumet le résultat au Compilateur
    Proxy -> Compiler;
    // Le Compilateur passe aux Tests
    Compiler -> Tests;
    // Les Tests alimentent le Validateur sémantique
    Tests -> Validator;
    // Le Validateur transmet au moteur de confiance
    Validator -> Confidence;
    // La Confiance est évaluée par le Détecteur de conflits
    Confidence -> Conflict;
    // Le Détecteur de conflits transmet au Gestionnaire de versions
    Conflict -> Version;

    // Observabilité
    // L'Event Bus envoie les événements au Logger
    EventBus -> Logger;
    // L'Event Bus envoie les événements aux Métriques
    EventBus -> Metrics;
    // L'Event Bus envoie les événements au Replay
    EventBus -> Replay;
    // Les Métriques alimentent le Dashboard
    Metrics -> Dashboard;
    // Le Watchdog surveille le Scheduler
    Watchdog -> Scheduler;

    // Lien physique
    // OpenVINO s'exécute sur le GPU
    OpenVINO -> GPU [style=dashed];

    // === Liens inter-diagrammes (navigation) ===
    Nav_Scheduler [label="Scheduler", shape=plaintext, URL="scheduler/10_scheduler.svg"];
    Nav_Context [label="Context", shape=plaintext, URL="context/20_context.svg"];
    Nav_Services [label="Services", shape=plaintext, URL="services/30_services.svg"];
    Nav_Experts [label="Experts", shape=plaintext, URL="experts/40_experts.svg"];
    Nav_Validation [label="Validation", shape=plaintext, URL="validation/50_validation.svg"];
    Nav_Learning [label="Learning", shape=plaintext, URL="learning/60_learning.svg"];
    Nav_Observability [label="Observability", shape=plaintext, URL="observability/70_observability.svg"];

    // Placement invisible (en bas)
    { rank=sink; Nav_Scheduler; Nav_Context; Nav_Services; Nav_Experts; Nav_Validation; Nav_Learning; Nav_Observability; }
}
