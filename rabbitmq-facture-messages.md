# Documentation Technique - Messages RabbitMQ Factures

Ce document décrit la structure des messages JSON attendus par les consumers RabbitMQ pour l'intégration des factures dans Ediflux.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Consumer MyEkivox/Ediflux (FluxExportDocument)](#consumer-myekivoxediflux-fluxexportdocument)
3. [Consumer Kinexo (KinexoFactureDTO)](#consumer-kinexo-kinexofacturedto)
4. [Énumérations](#énumérations)
5. [Configuration RabbitMQ](#configuration-rabbitmq)

---

## Vue d'ensemble

Ediflux dispose de deux consumers RabbitMQ pour l'intégration des factures :

| Consumer | Queue Property | Description |
|----------|----------------|-------------|
| `FactureMessageConsumer` | `myekivox-ediflux.rabbitmq.queue` | Intégration des factures depuis MyEkivox/MyKinexo |
| `KinexoFactureConsumer` | `kinexo-ediflux.rabbitmq.queue` | Intégration des factures depuis le système Kinexo |

Les deux consumers sont conditionnels et ne s'activent que si leur propriété de queue respective est configurée.

---

## Consumer MyEkivox/Ediflux (FluxExportDocument)

### Classe Java
`fr.cerfrance.edi.messagebroker.consumer.FactureMessageConsumer`

### Queue
Configurée via la propriété : `myekivox-ediflux.rabbitmq.queue`

### Structure du message JSON

```json
{
  "numeroDossier": "string",
  "idDocument": "string",
  "typeDocument": "string",
  "origine": "string",
  "kanalyseActif": boolean,
  "document": {
    "nom": "string",
    "typeMime": "string",
    "url": "string",
    "urlV2": "string",
    "dateEffet": "YYYY-MM-DD",
    "origine": "string"
  }
}
```

### Détail des champs

#### FluxExportDocument (racine)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `numeroDossier` | `String` | Oui | Identifiant unique du dossier client |
| `idDocument` | `String` | Oui | Identifiant unique du document dans le système source |
| `typeDocument` | `String` | Oui | Type de document (voir [valeurs acceptées](#types-de-documents-acceptés)) |
| `origine` | `String` | Non | Origine du document (utilisé pour filtrage/exclusion) |
| `kanalyseActif` | `boolean` | Oui | Indicateur d'activation de l'analyse Kanalyse. Si `false`, le document est ignoré |
| `document` | `DocumentMessageDTO` | Oui | Objet contenant les métadonnées du document |

#### DocumentMessageDTO (objet imbriqué)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `nom` | `String` | Oui | Nom du fichier document |
| `typeMime` | `String` | Non | Type MIME du document (ex: `application/pdf`) |
| `url` | `String` | Non | URL de téléchargement du document (version 1) |
| `urlV2` | `String` | Oui | URL de téléchargement du document (version 2, utilisée pour l'intégration) |
| `dateEffet` | `LocalDate` | Non | Date d'effet du document. Format ISO: `YYYY-MM-DD` |
| `origine` | `String` | Non | Origine spécifique du document |

### Types de documents acceptés

Les types de documents sont configurés via les paramètres divers de l'application :

#### Types Achat (FLUX_FACTURE_TYPES_ACHAT)
- `FACTURE_FOURNISSEUR` - Facture fournisseur
- `TICKET_CARBURANT` - Ticket de carburant
- `TICKET_DEPLACEMENT_PEAGE` - Ticket de péage
- `TICKET_SUPERMARCHE` - Ticket de supermarché
- `TICKET_RESTAURANT_HOTEL` - Ticket restaurant/hôtel
- `TICKET_DIVERS` - Autres tickets

#### Types Vente (FLUX_FACTURE_TYPES_VENTE)
- `FACTURE_CLIENT` - Facture client

> **Note**: Ces valeurs sont configurables et peuvent varier selon l'environnement.

### Règles de validation

Un document est traité uniquement si **toutes** les conditions suivantes sont remplies :

1. `kanalyseActif` est `true`
2. `typeDocument` fait partie des types acceptés (achat ou vente)
3. `origine` n'est pas dans la liste des origines exclues (`FLUX_FACTURE_ORIGINES_EXCLUSIONS`)

### Exemple de message valide

```json
{
  "numeroDossier": "12345",
  "idDocument": "DOC-2024-001234",
  "typeDocument": "FACTURE_FOURNISSEUR",
  "origine": "MYKINEXO",
  "kanalyseActif": true,
  "document": {
    "nom": "facture_fournisseur_2024.pdf",
    "typeMime": "application/pdf",
    "url": "https://storage.example.com/v1/documents/abc123",
    "urlV2": "https://storage.example.com/v2/documents/abc123",
    "dateEffet": "2024-01-15",
    "origine": "SCAN"
  }
}
```

---

## Consumer Kinexo (KinexoFactureDTO)

### Classe Java
`fr.cerfrance.edi.messagebroker.consumer.KinexoFactureConsumer`

### Queue
Configurée via la propriété : `kinexo-ediflux.rabbitmq.queue`

### Structure du message JSON

```json
{
  "reference": "string",
  "date": "YYYY-MM-DD",
  "numeroDossier": "string",
  "totalTTC": integer,
  "societe": "string",
  "societeId": "string",
  "pdfId": "string",
  "siret": "string",
  "libelleCatalogue": "string",
  "lignes": [
    {
      "designation": "string",
      "quantite": number,
      "prixUnitaireHT": integer,
      "montantHT": integer,
      "codeTauxTva": "string",
      "valeurTauxTva": integer,
      "prestation": {
        "code": "string",
        "libelle": "string",
        "domaine": "string",
        "quantite": number
      }
    }
  ]
}
```

### Détail des champs

#### KinexoFactureDTO (racine)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `reference` | `String` | Oui | Référence unique de la facture |
| `date` | `LocalDate` | Oui | Date de la facture. Format ISO: `YYYY-MM-DD` |
| `numeroDossier` | `String` | Oui | Identifiant du dossier client |
| `totalTTC` | `int` | Oui | Montant total TTC **en centimes** (ex: 15000 = 150,00€) |
| `societe` | `String` | Non | Nom de la société émettrice |
| `societeId` | `String` | Non | Identifiant de la société émettrice |
| `pdfId` | `String` | Oui | Identifiant du document PDF associé (utilisé pour le logging) |
| `siret` | `String` | Non | Numéro SIRET de la société |
| `libelleCatalogue` | `String` | Non | Libellé du catalogue de prestations |
| `lignes` | `List<LigneFactureDTO>` | Non | Liste des lignes de la facture |

#### LigneFactureDTO (ligne de facture)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `designation` | `String` | Oui | Libellé/désignation de la ligne |
| `quantite` | `Double` | Non | Quantité (peut être décimale) |
| `prixUnitaireHT` | `int` | Oui | Prix unitaire HT **en centimes** |
| `montantHT` | `int` | Oui | Montant total HT de la ligne **en centimes** |
| `codeTauxTva` | `String` | Non | Code du taux de TVA applicable |
| `valeurTauxTva` | `int` | Oui | Taux de TVA **en centièmes** (ex: 2000 = 20,00%) |
| `prestation` | `PrestationDTO` | Non | Détails de la prestation associée |

#### PrestationDTO (prestation)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `code` | `String` | Non | Code de la prestation |
| `libelle` | `String` | Non | Libellé de la prestation |
| `domaine` | `String` | Non | Domaine/catégorie de la prestation |
| `quantite` | `Double` | Non | Quantité de prestation (peut être décimale) |

### Conventions de montants

> **Important**: Tous les montants sont exprimés en **centimes** (ou centièmes pour les taux).

| Type | Unité | Exemple valeur | Équivalent réel |
|------|-------|----------------|-----------------|
| Montants (TTC, HT) | Centimes | `15000` | 150,00 € |
| Prix unitaires | Centimes | `2500` | 25,00 € |
| Taux TVA | Centièmes | `2000` | 20,00 % |
| Taux TVA | Centièmes | `550` | 5,50 % |

### Exemple de message valide

```json
{
  "reference": "FAC-2024-00123",
  "date": "2024-01-15",
  "numeroDossier": "12345",
  "totalTTC": 18000,
  "societe": "Kinexo Services",
  "societeId": "KNX001",
  "pdfId": "PDF-ABC123",
  "siret": "12345678901234",
  "libelleCatalogue": "Prestations comptables",
  "lignes": [
    {
      "designation": "Prestation comptabilité mensuelle",
      "quantite": 1.0,
      "prixUnitaireHT": 15000,
      "montantHT": 15000,
      "codeTauxTva": "TVA_20",
      "valeurTauxTva": 2000,
      "prestation": {
        "code": "COMPTA_MENS",
        "libelle": "Comptabilité mensuelle",
        "domaine": "COMPTABILITE",
        "quantite": 1.0
      }
    }
  ]
}
```

---

## Énumérations

### TypeFacture

Classe Java : `fr.cerfrance.edi.profil.model.facture.TypeFacture`

| Valeur | Description | Code numérique |
|--------|-------------|----------------|
| `ACHAT` | Facture d'achat (fournisseur) | 6 |
| `VENTE` | Facture de vente (client) | 7 |

### SensDocument

Classe Java : `fr.cerfrance.edi.messagebroker.enums.SensDocument`

| Valeur | Code | Description |
|--------|------|-------------|
| `SENS_ACHAT` | A | Document d'achat |
| `SENS_VENTE` | V | Document de vente |

### FichierOrigine

Classe Java : `fr.cerfrance.edi.profil.model.ecriture.FichierOrigine`

| Valeur | Description |
|--------|-------------|
| `KINEXO` | Origine système Kinexo |
| `MYKINEXO` | Origine système MyKinexo/MyEkivox |

---

## Configuration RabbitMQ

### Propriétés requises

#### Consumer MyEkivox/Ediflux

```properties
myekivox-ediflux.rabbitmq.queue=nom-de-la-queue
myekivox-ediflux.rabbitmq.topic=nom-du-topic-exchange
myekivox-ediflux.rabbitmq.routingkey=routing-key
```

#### Consumer Kinexo

```properties
kinexo-ediflux.rabbitmq.queue=nom-de-la-queue
kinexo-ediflux.rabbitmq.topic=nom-du-topic-exchange
kinexo-ediflux.rabbitmq.routingkey=routing-key
```

### Gestion des erreurs (Dead Letter Queue)

En cas d'erreur lors du traitement d'un message, celui-ci est automatiquement redirigé vers une Dead Letter Queue (DLQ) :

| Queue principale | DLQ |
|-----------------|-----|
| `${myekivox-ediflux.rabbitmq.queue}` | `${myekivox-ediflux.rabbitmq.queue}.dlq` |
| `${kinexo-ediflux.rabbitmq.queue}` | `${kinexo-ediflux.rabbitmq.queue}.dlq` |

### Concurrence

- **FactureMessageConsumer** : 5 consumers concurrents (`concurrency = "5"`)
- **KinexoFactureConsumer** : 1 consumer (par défaut)

---

## Références

### Fichiers sources

| Composant | Chemin |
|-----------|--------|
| FactureMessageConsumer | `back/src/main/java/fr/cerfrance/edi/messagebroker/consumer/FactureMessageConsumer.java` |
| KinexoFactureConsumer | `back/src/main/java/fr/cerfrance/edi/messagebroker/consumer/KinexoFactureConsumer.java` |
| FluxExportDocument | `back/src/main/java/fr/cerfrance/edi/messagebroker/dto/FluxExportDocument.java` |
| DocumentMessageDTO | `back/src/main/java/fr/cerfrance/edi/messagebroker/dto/DocumentMessageDTO.java` |
| KinexoFactureDTO | `back/src/main/java/fr/cerfrance/edi/messagebroker/dto/kinexo/KinexoFactureDTO.java` |
| LigneFactureDTO | `back/src/main/java/fr/cerfrance/edi/messagebroker/dto/kinexo/LigneFactureDTO.java` |
| PrestationDTO | `back/src/main/java/fr/cerfrance/edi/messagebroker/dto/kinexo/PrestationDTO.java` |
| TypeFacture | `back/src/main/java/fr/cerfrance/edi/profil/model/facture/TypeFacture.java` |
| SensDocument | `back/src/main/java/fr/cerfrance/edi/messagebroker/enums/SensDocument.java` |
| FichierOrigine | `back/src/main/java/fr/cerfrance/edi/profil/model/ecriture/FichierOrigine.java` |

### Configuration

Les configurations de queues et topics sont définies dans :
- `FactureMessageBrokerConfig.java`
- `KinexoFactureMessageBrokerConfig.java`

Les types de documents acceptés sont configurés dans les paramètres divers :
- `FLUX_FACTURE_TYPES_ACHAT`
- `FLUX_FACTURE_TYPES_VENTE`
- `FLUX_FACTURE_ORIGINES_EXCLUSIONS`
