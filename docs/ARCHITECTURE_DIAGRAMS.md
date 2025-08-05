# 🏗️ SPOTS Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    subgraph "Data Sources"
        IG[Instagram]
        FB[Facebook]
        RD[Reddit]
        OSM[OpenStreetMap]
        IGN[IGN Services]
    end
    
    subgraph "Data Collection Layer"
        PS[Playwright Scraper]
        AS[API Scrapers]
        GC[Geocoding Service]
    end
    
    subgraph "Backend Services"
        FA[FastAPI Application]
        DB[(SQLite Database)]
        DS[Data Services]
        ES[Enrichment Services]
    end
    
    subgraph "Frontend Application"
        LM[Leaflet Maps]
        RM[Regional Map]
        PM[Premium Map]
        API[API Service]
    end
    
    subgraph "External APIs"
        OM[Open-Meteo]
        GP[Géoplateforme]
        BAN[Base Adresse Nationale]
    end
    
    %% Data flow
    IG --> PS
    FB --> PS
    RD --> AS
    OSM --> AS
    
    PS --> DS
    AS --> DS
    DS --> DB
    
    DB --> FA
    ES --> FA
    
    FA --> API
    API --> LM
    API --> RM
    API --> PM
    
    IGN --> GP
    GP --> ES
    BAN --> GC
    GC --> ES
    OM --> FA
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Database
    participant IGN
    participant Weather
    
    User->>Frontend: Open Regional Map
    Frontend->>API: GET /api/spots
    API->>Database: Query spots
    Database-->>API: Return 817 spots
    API-->>Frontend: JSON response
    Frontend->>Frontend: Render markers
    
    User->>Frontend: Click on spot
    Frontend->>API: GET /api/spots/{id}
    API->>Database: Get spot details
    API->>IGN: Get elevation
    IGN-->>API: Elevation data
    API->>Weather: Get conditions
    Weather-->>API: Weather data
    API-->>Frontend: Enriched spot data
    Frontend-->>User: Display popup
```

## Database Schema

```mermaid
erDiagram
    SPOTS {
        int id PK
        string name
        float latitude
        float longitude
        string type
        string description
        string department
        float elevation
        bool verified
        float confidence_score
        datetime created_at
        datetime updated_at
    }
    
    WEATHER_CACHE {
        int id PK
        int spot_id FK
        float temperature
        string conditions
        datetime cached_at
    }
    
    USER_SPOTS {
        int id PK
        int user_id
        int spot_id FK
        bool favorite
        string notes
        datetime visited_at
    }
    
    SPOTS ||--o{ WEATHER_CACHE : has
    SPOTS ||--o{ USER_SPOTS : bookmarked_by
```

## Component Architecture

```mermaid
graph LR
    subgraph "Frontend Modules"
        MI[map-init.js]
        MC[map-controller.js]
        MV[map-visualization.js]
        MP[map-providers.js]
        HS[hidden-spots-loader.js]
        AS[api-service.js]
    end
    
    subgraph "Backend Modules"
        MA[main.py]
        AR[api/routes.py]
        SC[scrapers/]
        SV[services/]
        MD[models.py]
    end
    
    MI --> MC
    MC --> MV
    MC --> MP
    HS --> AS
    AS -.-> MA
    MA --> AR
    AR --> SV
    SV --> MD
```

## IGN Services Integration

```mermaid
graph TD
    subgraph "IGN Géoplateforme"
        WMTS[WMTS Service]
        WMS[WMS Service]
        WFS[WFS Service]
        ELEV[Elevation API]
        GEO[Geocoding API]
        ISO[Isochrone API]
    end
    
    subgraph "SPOTS Integration"
        TL[Tile Layers]
        FE[Feature Extraction]
        EE[Elevation Enrichment]
        AC[Address Conversion]
        RA[Reachability Analysis]
    end
    
    WMTS --> TL
    WMS --> TL
    WFS --> FE
    ELEV --> EE
    GEO --> AC
    ISO --> RA
    
    TL --> |Map Display| Frontend
    FE --> |Nearby Features| Backend
    EE --> |Spot Enrichment| Backend
    AC --> |Geocoding| Backend
    RA --> |Accessibility| Backend
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        LD[Local Development]
        LD --> |git push| GH[GitHub]
    end
    
    subgraph "CI/CD"
        GH --> |webhook| GA[GitHub Actions]
        GA --> |build| DI[Docker Image]
        GA --> |test| TS[Test Suite]
    end
    
    subgraph "Production"
        DI --> |deploy| DC[Docker Container]
        DC --> NG[Nginx Reverse Proxy]
        DC --> PG[(PostgreSQL)]
        NG --> CF[Cloudflare CDN]
    end
    
    subgraph "Monitoring"
        DC --> |logs| LG[Logging Service]
        DC --> |metrics| PM[Prometheus]
        PM --> GF[Grafana]
        DC --> |errors| ST[Sentry]
    end
```

## API Request Flow

```mermaid
flowchart TD
    A[Client Request] --> B{CORS Check}
    B -->|Pass| C[Route Handler]
    B -->|Fail| D[CORS Error]
    
    C --> E{Auth Required?}
    E -->|Yes| F[Validate Token]
    E -->|No| G[Process Request]
    
    F -->|Valid| G
    F -->|Invalid| H[401 Unauthorized]
    
    G --> I{Query Database}
    I -->|Success| J[Transform Data]
    I -->|Error| K[500 Error]
    
    J --> L{Enrich Data?}
    L -->|Yes| M[Call IGN/Weather]
    L -->|No| N[Return Response]
    
    M -->|Success| N
    M -->|Fail| O[Partial Response]
    
    N --> P[JSON Response]
    O --> P
```

## State Management Flow

```mermaid
stateDiagram-v2
    [*] --> Loading
    Loading --> LoadingSpots
    LoadingSpots --> LoadingWeather
    LoadingWeather --> Ready
    
    Ready --> FilteringDepartment
    Ready --> FilteringType
    Ready --> SearchingSpots
    
    FilteringDepartment --> UpdateMap
    FilteringType --> UpdateMap
    SearchingSpots --> UpdateMap
    
    UpdateMap --> Ready
    
    Ready --> ViewingSpot
    ViewingSpot --> LoadingDetails
    LoadingDetails --> ShowingPopup
    ShowingPopup --> Ready
    
    Ready --> Error
    Error --> Ready
```

## Performance Optimization Strategy

```mermaid
graph LR
    subgraph "Data Loading"
        A[Initial Load] --> B[Cluster Markers]
        B --> C[Lazy Load Details]
        C --> D[Cache Results]
    end
    
    subgraph "Map Rendering"
        E[Zoom Level] --> F{Zoom < 10?}
        F -->|Yes| G[Show Clusters]
        F -->|No| H[Show Markers]
        H --> I{Zoom > 14?}
        I -->|Yes| J[Load Satellite]
        I -->|No| K[Show Topo]
    end
    
    subgraph "API Optimization"
        L[Request] --> M[Check Cache]
        M -->|Hit| N[Return Cached]
        M -->|Miss| O[Fetch Data]
        O --> P[Update Cache]
        P --> N
    end
```

---

These diagrams provide a visual understanding of the SPOTS architecture, making it easier to understand the system's components and their interactions. They can be rendered in any Markdown viewer that supports Mermaid syntax.
