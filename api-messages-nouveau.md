# API /api/messages?type=nouveau

Documentation pour l'implémentation d'un appel distant vers l'endpoint d'injection de messages RabbitMQ.

## Endpoint

```
POST /api/messages?type=nouveau
```

## Description

Cet endpoint permet d'injecter un nouveau message dans RabbitMQ via l'exchange topic `uninov.topic`. Le message sera routé vers les queues correspondantes selon la `routingKey` fournie.

## Authentification

### Prérequis

1. **Token JWT OAuth2** : L'API utilise OAuth2 Resource Server. Un token JWT valide doit être fourni dans le header `Authorization`.

2. **Rôle requis** : L'utilisateur doit posséder le rôle `ROLE_MAINTENANCE` dans son token JWT.

3. **CSRF** (si activé) : En environnement de production, la protection CSRF est activée. Un token CSRF doit être récupéré et envoyé.

### Headers HTTP requis

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

Si CSRF est activé (production) :
```http
X-XSRF-TOKEN: <CSRF_TOKEN>
Cookie: XSRF-TOKEN=<CSRF_TOKEN>
```

## Corps de la requête

### Structure JSON

```json
{
  "routingKey": "string",
  "message": {
    "contentType": "string",
    "headers": {
      "key1": "value1",
      "key2": "value2"
    },
    "payload": "string"
  }
}
```

### Champs

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `routingKey` | string | Oui | Clé de routage RabbitMQ pour l'exchange topic. Détermine vers quelle(s) queue(s) le message sera envoyé. |
| `message.contentType` | string | Non | Type MIME du contenu. Défaut : `application/json` |
| `message.headers` | object | Non | Headers personnalisés à ajouter au message AMQP. Défaut : `{}` |
| `message.payload` | string | Oui | Contenu du message (généralement du JSON stringifié). |

### Validation

- `routingKey` : ne doit pas être vide (`@NotBlank`)
- `message` : ne doit pas être null (`@NotNull`)
- `message.payload` : ne doit pas être vide (`@NotBlank`)

## Réponse

### Succès

```
HTTP 200 OK
```

Corps vide (l'endpoint retourne `void`).

### Erreurs

| Code | Description |
|------|-------------|
| 400 | Requête invalide (validation échouée) |
| 401 | Non authentifié (token JWT manquant ou invalide) |
| 403 | Non autorisé (rôle `ROLE_MAINTENANCE` manquant) |

## Exemples d'implémentation

### cURL

```bash
curl -X POST "https://<HOST>/api/messages?type=nouveau" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "routingKey": "mon.service.action",
    "message": {
      "contentType": "application/json",
      "headers": {},
      "payload": "{\"id\": 123, \"action\": \"process\"}"
    }
  }'
```

### TypeScript/JavaScript (Axios)

```typescript
import axios from 'axios';

interface Message {
  contentType?: string;
  headers?: Record<string, string>;
  payload: string;
}

interface NouveauMessage {
  routingKey: string;
  message: Message;
}

async function injecterMessage(token: string, data: NouveauMessage): Promise<void> {
  await axios.post(
    `${BASE_URL}/api/messages?type=nouveau`,
    data,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
}

// Utilisation
const message: NouveauMessage = {
  routingKey: 'mon.service.action',
  message: {
    contentType: 'application/json',
    headers: {},
    payload: JSON.stringify({ id: 123, action: 'process' })
  }
};

await injecterMessage(jwtToken, message);
```

### Java (Spring WebClient)

```java
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

public class MaintenanceApiClient {

    private final WebClient webClient;

    public MaintenanceApiClient(String baseUrl, String jwtToken) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader("Authorization", "Bearer " + jwtToken)
            .defaultHeader("Content-Type", "application/json")
            .build();
    }

    public Mono<Void> injecterMessage(InjectionMessageDTO message) {
        return webClient.post()
            .uri(uriBuilder -> uriBuilder
                .path("/api/messages")
                .queryParam("type", "nouveau")
                .build())
            .bodyValue(message)
            .retrieve()
            .bodyToMono(Void.class);
    }
}
```

### Java (RestTemplate)

```java
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

public class MaintenanceApiClient {

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public void injecterMessage(String jwtToken, InjectionMessageDTO message) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(jwtToken);
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<InjectionMessageDTO> request = new HttpEntity<>(message, headers);

        String url = UriComponentsBuilder.fromHttpUrl(baseUrl)
            .path("/api/messages")
            .queryParam("type", "nouveau")
            .toUriString();

        restTemplate.postForEntity(url, request, Void.class);
    }
}
```

### Python (requests)

```python
import requests
import json

def injecter_message(base_url: str, jwt_token: str, routing_key: str, payload: dict) -> None:
    url = f"{base_url}/api/messages"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    data = {
        "routingKey": routing_key,
        "message": {
            "contentType": "application/json",
            "headers": {},
            "payload": json.dumps(payload)
        }
    }

    response = requests.post(
        url,
        params={"type": "nouveau"},
        headers=headers,
        json=data
    )

    response.raise_for_status()

# Utilisation
injecter_message(
    base_url="https://maintenance.example.com",
    jwt_token="eyJhbGciOiJSUzI1NiIsInR5cCI6...",
    routing_key="mon.service.action",
    payload={"id": 123, "action": "process"}
)
```

## Prérequis de développement

### 1. Obtention du token JWT

Le token JWT doit être obtenu auprès du serveur d'authentification OAuth2/Keycloak configuré pour l'environnement cible. Le token doit contenir :
- Le claim de rôles incluant `ROLE_MAINTENANCE`
- Une durée de validité non expirée

### 2. Configuration réseau

- L'application appelante doit avoir accès réseau à l'API kinexo-maintenance
- Configurer les timeouts appropriés pour les appels HTTP

### 3. Gestion des erreurs

Implémenter la gestion des codes d'erreur HTTP :
- Retry avec backoff exponentiel pour les erreurs 5xx
- Pas de retry pour les erreurs 4xx (erreurs client)
- Logging des erreurs pour le debugging

### 4. Sérialisation du payload

Le champ `payload` est une chaîne de caractères. Si le message contient du JSON, il doit être sérialisé en string avant l'envoi :

```typescript
// Correct
payload: JSON.stringify({ id: 123, data: "value" })

// Incorrect - ne pas envoyer un objet directement
payload: { id: 123, data: "value" }
```

## Comportement interne

Après réception de la requête, le service :

1. Valide le corps de la requête (Jakarta Validation)
2. Construit un message AMQP avec le payload et les headers fournis
3. Ajoute automatiquement le header d'autorisation du contexte courant
4. Publie le message sur l'exchange `uninov.topic` avec la routingKey spécifiée

Le message sera ensuite routé vers les queues RabbitMQ dont le binding correspond à la routingKey.
