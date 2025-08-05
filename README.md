# 🗺️ Spots Secrets - Occitanie

Système de découverte et suivi des spots secrets dans la région Occitanie avec intégration météo en temps réel.

## 📚 Documentation

La documentation complète est maintenant organisée dans le répertoire `/docs` :
- **[📖 Guides](./docs/guides/)** - Guides d'implémentation et tutoriels
- **[📊 Rapports](./docs/reports/)** - Analyses et revues de code
- **[📋 Résumés](./docs/summaries/)** - Vues d'ensemble du projet
- **[🔧 Technique](./docs/technical/)** - Documentation technique
- **[📄 Index Complet](./docs/README.md)** - Vue d'ensemble de toute la documentation

## ✨ Fonctionnalités

### 🔍 Découverte Multi-Départementale
- **8 départements couverts** : Ariège, Aveyron, Haute-Garonne, Gers, Lot, Hautes-Pyrénées, Tarn, Tarn-et-Garonne
- Scraping automatisé depuis Reddit, Instagram, OpenStreetMap
- Traitement du langage naturel pour l'extraction des lieux
- Validation GPS et géocodage
- Détection des doublons et contrôle qualité

### 🌤️ Intégration Météo Régionale
- Données météo en temps réel via Open-Meteo API
- **10 stations météo** réparties dans toute la région
- Recommandations d'activités selon la météo
- Prévisions sur 7 jours par zone
- Alertes météo pour les spots sensibles

### 🗺️ Cartographie Premium
- **IGN officiel** : Cartes satellites et topographiques françaises
- ESRI World Imagery pour la haute résolution
- Cartes spécialisées : randonnée, cyclisme, topographie
- Clustering intelligent des marqueurs
- Export GPX pour GPS

### 📊 Analyse Régionale
- Répartition des spots par département
- Zones d'intérêt : Pyrénées, Causses, Montagne Noire, Aubrac
- Statistiques détaillées par type d'activité
- Filtrage par département et caractéristiques

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.8+
- Node.js 18+
- SQLite3

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/yourusername/spots-secrets-occitanie.git
cd spots-secrets-occitanie

# Lancer le script de configuration
./scripts/setup.sh

# Démarrer l'application
./scripts/start.sh
```

### Accès

- **Carte régionale** : http://localhost:8085/regional-map.html
- **Carte premium** : http://localhost:8085/premium-map.html
- **API** : http://localhost:8000/docs

## 🏔️ Zones Couvertes

### Pyrénées (Ariège, Hautes-Pyrénées)
- Randonnée haute montagne
- Lacs d'altitude
- Stations thermales
- Grottes et gouffres

### Causses et Gorges (Lot, Aveyron)
- Canyoning
- Spéléologie
- Villages perchés
- Sites de parapente

### Montagne Noire (Tarn)
- Forêts denses
- Lacs de montagne
- Sentiers VTT
- Patrimoine cathare

### Plaines et Coteaux (Gers, Tarn-et-Garonne)
- Bastides médiévales
- Routes des vins
- Canal du Midi
- Patrimoine gascon

## 📈 Données

- **3,226 spots** répertoriés
- **8 départements** couverts
- **10 stations météo** actives
- **Mise à jour** : temps réel pour la météo

## 🛠️ Technologies

- **Backend** : Python, FastAPI, SQLAlchemy
- **Frontend** : JavaScript, Leaflet.js
- **Cartes** : IGN France, ESRI, OpenStreetMap
- **Météo** : Open-Meteo API
- **Base de données** : SQLite

## 📱 Application Progressive Web

- Fonctionnement hors ligne
- Interface mobile optimisée
- Synchronisation en arrière-plan
- Notifications push pour alertes météo

## 🤝 Contribution

Les contributions sont bienvenues ! Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour les directives.

## 📄 Licence

Ce projet est sous licence MIT - voir [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- IGN France pour les cartes officielles
- Open-Meteo pour les données météo
- Communauté OpenStreetMap
- Contributeurs Reddit et réseaux sociaux
