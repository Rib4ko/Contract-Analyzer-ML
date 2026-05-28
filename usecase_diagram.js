// Mermaid Use Case Diagram for Lexa Audit (Legal ML)
// Exported as a string that can be injected into a Mermaid container.

export const useCaseDiagram = `
usecaseDiagram
    actor "Avocat (Utilisateur)" as User
    actor "Supabase (Auth & DB)" as Supabase
    actor "Modèles ML Locaux" as LocalML
    actor "Groq API (LLM Cloud)" as Groq

    package "Lexa Audit Platform" {
        usecase "S'authentifier" as UC_Auth
        usecase "Gérer Playbook" as UC_Playbook
        usecase "Activer le mode Air‑Gapped" as UC_AirGap
        usecase "Auditer un Contrat" as UC_Audit
        usecase "Exporter Rapport (DOCX)" as UC_Export
        usecase "Extraction & OCR" as UC_OCR
        usecase "Classification SVM" as UC_Classify
        usecase "Déviation Playbook (TF‑IDF)" as UC_Deviate
        usecase "Validation Définitions" as UC_Defs
        usecase "Extraction de faits" as UC_Facts
    }

    %% Relations utilisateur
    User --> UC_Auth
    User --> UC_Playbook
    User --> UC_AirGap
    User --> UC_Audit
    User --> UC_Export

    %% Inclusions (include) dans l'audit
    UC_Audit ..> UC_OCR   : <<include>>
    UC_Audit ..> UC_Classify : <<include>>
    UC_Audit ..> UC_Deviate : <<include>>
    UC_Audit ..> UC_Defs   : <<include>>
    UC_Audit ..> UC_Facts  : <<include>>

    %% Extension du mode Air‑Gapped (bloque le cloud)
    UC_AirGap ..> UC_Facts : <<extends>> (bloque l'accès au cloud)

    %% Interactions externes
    UC_Auth --> Supabase
    UC_Playbook --> Supabase
    UC_Classify --> LocalML
    UC_Deviate --> LocalML
    UC_Defs --> LocalML
    UC_Facts --> Groq
`;

// Example usage (in a React component, for instance):
// import { useEffect } from 'react';
// import mermaid from 'mermaid';
// import { useCaseDiagram } from './usecase_diagram';
// useEffect(() => {
//   mermaid.initialize({ startOnLoad: true, theme: 'dark' });
//   mermaid.contentLoaded();
// }, []);

// Then in JSX:
// <div className="mermaid">{useCaseDiagram}</div>
