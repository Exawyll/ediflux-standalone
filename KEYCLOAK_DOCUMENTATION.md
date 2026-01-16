Documentation : Implémentation d'une authentification Keycloak pour appels API sécurisés

  Contexte et objectif

  Cette documentation décrit comment implémenter une brique d'authentification Keycloak permettant à une application Python d'obtenir un token OAuth2 pour appeler des APIs sécurisées. L'architecture supporte deux flux d'authentification :

  1. Client Credentials Flow : Pour les appels service-to-service (backend → API)
  2. Authorization Code Flow : Pour l'authentification utilisateur via navigateur

  ---
  1. Architecture générale

  1.1 Flux Client Credentials (Service-to-Service)

  ┌─────────────┐     1. POST /token          ┌──────────────┐
  │             │     grant_type=client_creds │              │
  │  Votre App  │ ──────────────────────────► │   Keycloak   │
  │  (Backend)  │                             │   Server     │
  │             │ ◄────────────────────────── │              │
  └─────────────┘     2. access_token (JWT)   └──────────────┘
         │
         │ 3. Authorization: Bearer <token>
         ▼
  ┌─────────────┐
  │  API Cible  │
  │  (Protégée) │
  └─────────────┘

  1.2 Endpoint Keycloak à utiliser

  POST {KEYCLOAK_SERVER_URL}/realms/{REALM_NAME}/protocol/openid-connect/token

  ---
  2. Configuration requise

  2.1 Variables d'environnement

  Définir ces variables pour chaque environnement/client :

  # Configuration Keycloak
  KEYCLOAK_SERVER_URL=https://auth.example.com/auth
  KEYCLOAK_REALM_NAME=mon-realm
  KEYCLOAK_CLIENT_ID=mon-application
  KEYCLOAK_CLIENT_SECRET=secret-du-client

  # Configuration API cible (optionnel - si API différente)
  API_BASE_URL=https://api.example.com

  2.2 Prérequis côté Keycloak

  Le client Keycloak doit être configuré avec :
  - Access Type : confidential (pour avoir un client_secret)
  - Service Accounts Enabled : ON (pour le Client Credentials Flow)
  - Valid Redirect URIs : Configuré si Authorization Code Flow utilisé

  ---
  3. Implémentation Python

  3.1 Module d'authentification (auth/token.py)

  import os
  import requests
  from typing import Optional
  import logging

  logger = logging.getLogger(__name__)


  class AuthToken:
      """
      Gère l'obtention et le rafraîchissement des tokens Keycloak.
      
      Utilise le Client Credentials Flow pour l'authentification service-to-service.
      """

      def __init__(self, client_prefix: Optional[str] = None):
          """
          Initialise le gestionnaire de token.
          
          Args:
              client_prefix: Préfixe pour les variables d'environnement (ex: "ADHEO").
                            Si fourni, cherche {PREFIX}_KEYCLOAK_SERVER_URL, etc.
                            Sinon, utilise KEYCLOAK_SERVER_URL directement.
          """
          self.client_prefix = client_prefix
          self._load_config()

      def _get_env(self, key: str) -> str:
          """Récupère une variable d'environnement avec ou sans préfixe."""
          if self.client_prefix:
              prefixed_key = f"{self.client_prefix.upper()}_{key}"
              value = os.environ.get(prefixed_key)
              if value:
                  return value
          return os.environ.get(key, "")

      def _load_config(self):
          """Charge la configuration depuis les variables d'environnement."""
          self.server_url = self._get_env("KEYCLOAK_SERVER_URL")
          self.realm_name = self._get_env("KEYCLOAK_REALM_NAME")
          self.client_id = self._get_env("KEYCLOAK_CLIENT_ID")
          self.client_secret = self._get_env("KEYCLOAK_CLIENT_SECRET")

          # Validation
          if not all([self.server_url, self.realm_name, self.client_id, self.client_secret]):
              raise ValueError(
                  "Configuration Keycloak incomplète. "
                  "Vérifiez les variables: KEYCLOAK_SERVER_URL, KEYCLOAK_REALM_NAME, "
                  "KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET"
              )

      @property
      def token_endpoint(self) -> str:
          """Construit l'URL du endpoint token."""
          return f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/token"

      def get_token(self) -> dict:
          """
          Obtient un access token via Client Credentials Flow.
          
          Returns:
              dict: Réponse Keycloak contenant:
                  - access_token: Le JWT à utiliser
                  - expires_in: Durée de validité en secondes
                  - refresh_expires_in: Durée de validité du refresh token
                  - token_type: "Bearer"
                  
          Raises:
              requests.exceptions.HTTPError: Si la requête échoue
          """
          payload = {
              "grant_type": "client_credentials",
              "client_id": self.client_id,
              "client_secret": self.client_secret,
          }

          headers = {
              "Content-Type": "application/x-www-form-urlencoded"
          }

          logger.debug(f"Requesting token from {self.token_endpoint}")

          response = requests.post(
              self.token_endpoint,
              data=payload,
              headers=headers,
              verify=True  # Mettre False uniquement en dev si certificat auto-signé
          )

          response.raise_for_status()

          token_data = response.json()
          logger.info(f"Token obtained, expires in {token_data.get('expires_in')} seconds")

          return token_data

      def get_access_token(self) -> str:
          """
          Raccourci pour obtenir uniquement l'access_token.
          
          Returns:
              str: Le JWT access token
          """
          return self.get_token()["access_token"]

  3.2 Client API sécurisé (api/secure_client.py)

  import requests
  from typing import Optional, Dict, Any
  import logging
  from auth.token import AuthToken

  logger = logging.getLogger(__name__)


  class SecureAPIClient:
      """
      Client HTTP pour appeler des APIs protégées par Keycloak.
      
      Gère automatiquement l'obtention du token et son inclusion dans les requêtes.
      """

      def __init__(
          self,
          base_url: str,
          client_prefix: Optional[str] = None,
          verify_ssl: bool = True
      ):
          """
          Initialise le client API sécurisé.
          
          Args:
              base_url: URL de base de l'API (ex: "https://api.example.com")
              client_prefix: Préfixe pour les variables d'environnement Keycloak
              verify_ssl: Vérifier les certificats SSL (True en production)
          """
          self.base_url = base_url.rstrip("/")
          self.verify_ssl = verify_ssl
          self.auth_token = AuthToken(client_prefix)
          self._token: Optional[str] = None

      def _get_token(self) -> str:
          """Obtient ou réutilise le token d'accès."""
          if not self._token:
              self._token = self.auth_token.get_access_token()
          return self._token

      def _refresh_token(self):
          """Force le renouvellement du token."""
          self._token = None
          return self._get_token()

      def _build_headers(self, extra_headers: Optional[Dict] = None) -> Dict[str, str]:
          """
          Construit les headers HTTP avec le token Bearer.
          
          Args:
              extra_headers: Headers additionnels à inclure
              
          Returns:
              Dict avec Authorization et headers standards
          """
          headers = {
              "Authorization": f"Bearer {self._get_token()}",
              "Accept": "application/json",
          }

          if extra_headers:
              headers.update(extra_headers)

          return headers

      def get(
          self,
          endpoint: str,
          params: Optional[Dict] = None,
          headers: Optional[Dict] = None
      ) -> requests.Response:
          """
          Effectue une requête GET authentifiée.
          
          Args:
              endpoint: Chemin de l'endpoint (ex: "/api/users")
              params: Paramètres de requête
              headers: Headers additionnels
              
          Returns:
              Response object
          """
          url = f"{self.base_url}{endpoint}"

          response = requests.get(
              url,
              params=params,
              headers=self._build_headers(headers),
              verify=self.verify_ssl
          )

          # Si 401, tenter un refresh du token et réessayer
          if response.status_code == 401:
              logger.warning("Token expired, refreshing...")
              self._refresh_token()
              response = requests.get(
                  url,
                  params=params,
                  headers=self._build_headers(headers),
                  verify=self.verify_ssl
              )

          return response

      def post(
          self,
          endpoint: str,
          json_data: Optional[Dict] = None,
          data: Optional[Any] = None,
          headers: Optional[Dict] = None
      ) -> requests.Response:
          """
          Effectue une requête POST authentifiée.
          
          Args:
              endpoint: Chemin de l'endpoint
              json_data: Données JSON à envoyer
              data: Données brutes à envoyer
              headers: Headers additionnels
              
          Returns:
              Response object
          """
          url = f"{self.base_url}{endpoint}"

          request_headers = self._build_headers(headers)
          if json_data:
              request_headers["Content-Type"] = "application/json"

          response = requests.post(
              url,
              json=json_data,
              data=data,
              headers=request_headers,
              verify=self.verify_ssl
          )

          # Si 401, tenter un refresh du token et réessayer
          if response.status_code == 401:
              logger.warning("Token expired, refreshing...")
              self._refresh_token()
              response = requests.post(
                  url,
                  json=json_data,
                  data=data,
                  headers=self._build_headers(headers),
                  verify=self.verify_ssl
              )

          return response

      def put(
          self,
          endpoint: str,
          json_data: Optional[Dict] = None,
          headers: Optional[Dict] = None
      ) -> requests.Response:
          """Effectue une requête PUT authentifiée."""
          url = f"{self.base_url}{endpoint}"

          request_headers = self._build_headers(headers)
          request_headers["Content-Type"] = "application/json"

          response = requests.put(
              url,
              json=json_data,
              headers=request_headers,
              verify=self.verify_ssl
          )

          if response.status_code == 401:
              self._refresh_token()
              response = requests.put(
                  url,
                  json=json_data,
                  headers=self._build_headers(headers),
                  verify=self.verify_ssl
              )

          return response

      def delete(
          self,
          endpoint: str,
          headers: Optional[Dict] = None
      ) -> requests.Response:
          """Effectue une requête DELETE authentifiée."""
          url = f"{self.base_url}{endpoint}"

          response = requests.delete(
              url,
              headers=self._build_headers(headers),
              verify=self.verify_ssl
          )

          if response.status_code == 401:
              self._refresh_token()
              response = requests.delete(
                  url,
                  headers=self._build_headers(headers),
                  verify=self.verify_ssl
              )

          return response

  3.3 Gestion du token XSRF (si requis par l'API cible)

  Certaines APIs protégées par Spring Security exigent un token XSRF. Voici comment le gérer dynamiquement :

  class SecureAPIClientWithXSRF(SecureAPIClient):
      """
      Extension du client API avec gestion XSRF.
      
      Obtient dynamiquement le token XSRF depuis l'API avant les requêtes mutatives.
      """

      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self._xsrf_token: Optional[str] = None
          self._session = requests.Session()

      def _fetch_xsrf_token(self) -> str:
          """
          Récupère le token XSRF depuis l'API.
          
          Effectue une requête GET pour obtenir le cookie XSRF-TOKEN.
          """
          # Faire une requête GET pour obtenir le cookie XSRF
          response = self._session.get(
              f"{self.base_url}/api/health",  # Ou tout endpoint accessible
              headers={"Authorization": f"Bearer {self._get_token()}"},
              verify=self.verify_ssl
          )

          # Extraire le token du cookie
          xsrf_cookie = self._session.cookies.get("XSRF-TOKEN")
          if xsrf_cookie:
              self._xsrf_token = xsrf_cookie
              logger.debug(f"XSRF token obtained: {xsrf_cookie[:20]}...")

          return self._xsrf_token or ""

      def _build_headers(self, extra_headers: Optional[Dict] = None) -> Dict[str, str]:
          """Ajoute le header X-XSRF-TOKEN pour les requêtes mutatives."""
          headers = super()._build_headers(extra_headers)

          if self._xsrf_token:
              headers["X-XSRF-TOKEN"] = self._xsrf_token

          return headers

      def post(self, *args, **kwargs) -> requests.Response:
          """POST avec gestion XSRF."""
          if not self._xsrf_token:
              self._fetch_xsrf_token()
          return super().post(*args, **kwargs)

      def put(self, *args, **kwargs) -> requests.Response:
          """PUT avec gestion XSRF."""
          if not self._xsrf_token:
              self._fetch_xsrf_token()
          return super().put(*args, **kwargs)

      def delete(self, *args, **kwargs) -> requests.Response:
          """DELETE avec gestion XSRF."""
          if not self._xsrf_token:
              self._fetch_xsrf_token()
          return super().delete(*args, **kwargs)

  ---
  4. Utilisation

  4.1 Exemple basique

  import os
  from api.secure_client import SecureAPIClient

  # Configuration via variables d'environnement
  os.environ["KEYCLOAK_SERVER_URL"] = "https://auth.example.com/auth"
  os.environ["KEYCLOAK_REALM_NAME"] = "mon-realm"
  os.environ["KEYCLOAK_CLIENT_ID"] = "mon-app"
  os.environ["KEYCLOAK_CLIENT_SECRET"] = "mon-secret"

  # Créer le client
  client = SecureAPIClient(
      base_url="https://api.example.com",
      verify_ssl=True
  )

  # Appeler l'API
  response = client.get("/api/users")
  if response.ok:
      users = response.json()
      print(f"Trouvé {len(users)} utilisateurs")
  else:
      print(f"Erreur: {response.status_code} - {response.text}")

  # POST avec données JSON
  new_user = {"name": "Jean Dupont", "email": "jean@example.com"}
  response = client.post("/api/users", json_data=new_user)

  4.2 Exemple multi-tenant (plusieurs configurations Keycloak)

  # Variables d'environnement pour le client "ADHEO"
  os.environ["ADHEO_KEYCLOAK_SERVER_URL"] = "https://auth-adheo.example.com/auth"
  os.environ["ADHEO_KEYCLOAK_REALM_NAME"] = "adheo"
  os.environ["ADHEO_KEYCLOAK_CLIENT_ID"] = "app-adheo"
  os.environ["ADHEO_KEYCLOAK_CLIENT_SECRET"] = "secret-adheo"

  # Variables pour le client "BYEC"
  os.environ["BYEC_KEYCLOAK_SERVER_URL"] = "https://auth-byec.example.com/auth"
  os.environ["BYEC_KEYCLOAK_REALM_NAME"] = "byec"
  os.environ["BYEC_KEYCLOAK_CLIENT_ID"] = "app-byec"
  os.environ["BYEC_KEYCLOAK_CLIENT_SECRET"] = "secret-byec"

  # Créer des clients pour chaque tenant
  client_adheo = SecureAPIClient(
      base_url="https://api-adheo.example.com",
      client_prefix="ADHEO"
  )

  client_byec = SecureAPIClient(
      base_url="https://api-byec.example.com",
      client_prefix="BYEC"
  )

  ---
  5. Gestion des erreurs

  5.1 Erreurs courantes
  ┌──────┬──────────────────────────────────────┬────────────────────────────────────────────┐
  │ Code │                Cause                 │                  Solution                  │
  ├──────┼──────────────────────────────────────┼────────────────────────────────────────────┤
  │ 401  │ Token expiré ou invalide             │ Refresh automatique (implémenté)           │
  ├──────┼──────────────────────────────────────┼────────────────────────────────────────────┤
  │ 403  │ Permissions insuffisantes            │ Vérifier les rôles du client dans Keycloak │
  ├──────┼──────────────────────────────────────┼────────────────────────────────────────────┤
  │ 400  │ grant_type ou credentials incorrects │ Vérifier client_id et client_secret        │
  ├──────┼──────────────────────────────────────┼────────────────────────────────────────────┤
  │ 404  │ Realm inexistant                     │ Vérifier KEYCLOAK_REALM_NAME               │
  └──────┴──────────────────────────────────────┴────────────────────────────────────────────┘
  5.2 Classe d'exception personnalisée

  class KeycloakAuthError(Exception):
      """Erreur d'authentification Keycloak."""

      def __init__(self, message: str, status_code: int = None, response: dict = None):
          self.message = message
          self.status_code = status_code
          self.response = response
          super().__init__(self.message)


  def get_token_with_error_handling(auth: AuthToken) -> str:
      """Obtient un token avec gestion d'erreurs détaillée."""
      try:
          return auth.get_access_token()
      except requests.exceptions.HTTPError as e:
          error_data = {}
          try:
              error_data = e.response.json()
          except:
              pass

          if e.response.status_code == 401:
              raise KeycloakAuthError(
                  "Identifiants invalides (client_id ou client_secret)",
                  status_code=401,
                  response=error_data
              )
          elif e.response.status_code == 400:
              error_desc = error_data.get("error_description", "Unknown error")
              raise KeycloakAuthError(
                  f"Requête invalide: {error_desc}",
                  status_code=400,
                  response=error_data
              )
          else:
              raise KeycloakAuthError(
                  f"Erreur Keycloak: {e}",
                  status_code=e.response.status_code,
                  response=error_data
              )
      except requests.exceptions.ConnectionError:
          raise KeycloakAuthError("Impossible de contacter le serveur Keycloak")

  ---
  6. Tests

  6.1 Script de test de connectivité

  #!/usr/bin/env python3
  """
  Script de test de la connectivité Keycloak.

  Usage:
      python test_keycloak.py
  """

  import os
  import sys
  import requests
  import jwt  # pip install pyjwt

  def test_keycloak_connection():
      """Teste la connexion à Keycloak et l'obtention d'un token."""

      # Configuration
      server_url = os.environ.get("KEYCLOAK_SERVER_URL")
      realm = os.environ.get("KEYCLOAK_REALM_NAME")
      client_id = os.environ.get("KEYCLOAK_CLIENT_ID")
      client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET")

      print("=" * 60)
      print("TEST DE CONNECTIVITÉ KEYCLOAK")
      print("=" * 60)

      # 1. Test well-known endpoint
      print("\n1. Test du well-known endpoint...")
      well_known_url = f"{server_url}/realms/{realm}/.well-known/openid-configuration"

      try:
          response = requests.get(well_known_url, verify=False)
          response.raise_for_status()
          config = response.json()
          print(f"   ✓ Well-known accessible")
          print(f"   - Token endpoint: {config.get('token_endpoint')}")
          print(f"   - Issuer: {config.get('issuer')}")
      except Exception as e:
          print(f"   ✗ Échec: {e}")
          return False

      # 2. Test obtention token
      print("\n2. Test d'obtention du token...")
      token_url = f"{server_url}/realms/{realm}/protocol/openid-connect/token"

      try:
          response = requests.post(
              token_url,
              data={
                  "grant_type": "client_credentials",
                  "client_id": client_id,
                  "client_secret": client_secret,
              },
              verify=False
          )
          response.raise_for_status()
          token_data = response.json()
          access_token = token_data.get("access_token")
          print(f"   ✓ Token obtenu avec succès")
          print(f"   - Expire dans: {token_data.get('expires_in')} secondes")
          print(f"   - Type: {token_data.get('token_type')}")
      except requests.exceptions.HTTPError as e:
          print(f"   ✗ Échec HTTP {e.response.status_code}")
          try:
              error = e.response.json()
              print(f"   - Erreur: {error.get('error')}")
              print(f"   - Description: {error.get('error_description')}")
          except:
              print(f"   - Réponse: {e.response.text}")
          return False
      except Exception as e:
          print(f"   ✗ Échec: {e}")
          return False

      # 3. Décodage du token (sans vérification signature)
      print("\n3. Analyse du token JWT...")
      try:
          decoded = jwt.decode(access_token, options={"verify_signature": False})
          print(f"   - Issuer (iss): {decoded.get('iss')}")
          print(f"   - Subject (sub): {decoded.get('sub')}")
          print(f"   - Client ID (azp): {decoded.get('azp')}")
          print(f"   - Scopes: {decoded.get('scope')}")

          # Rôles
          realm_access = decoded.get("realm_access", {})
          if realm_access.get("roles"):
              print(f"   - Rôles realm: {realm_access.get('roles')}")

          resource_access = decoded.get("resource_access", {})
          if resource_access:
              print(f"   - Resource access: {list(resource_access.keys())}")
      except Exception as e:
          print(f"   ⚠ Impossible de décoder le token: {e}")

      print("\n" + "=" * 60)
      print("TEST RÉUSSI - La configuration Keycloak est fonctionnelle")
      print("=" * 60)

      return True


  if __name__ == "__main__":
      success = test_keycloak_connection()
      sys.exit(0 if success else 1)

  ---
  7. Dépendances Python

  # requirements.txt
  requests>=2.28.0
  PyJWT>=2.6.0
  python-keycloak>=2.6.0  # Optionnel, si utilisation de la librairie officielle

  ---
  8. Structure de fichiers recommandée

  mon_projet/
  ├── auth/
  │   ├── __init__.py
  │   └── token.py              # Classe AuthToken
  ├── api/
  │   ├── __init__.py
  │   └── secure_client.py      # Classe SecureAPIClient
  ├── config/
  │   ├── __init__.py
  │   └── settings.py           # Chargement configuration
  ├── tests/
  │   └── test_keycloak.py      # Script de test
  ├── .env.example              # Template de configuration
  ├── requirements.txt
  └── main.py

  ---
  9. Checklist d'implémentation

  - Créer le module auth/token.py avec la classe AuthToken
  - Créer le module api/secure_client.py avec la classe SecureAPIClient
  - Configurer les variables d'environnement Keycloak
  - Tester la connectivité avec le script de test
  - Vérifier que le client Keycloak a Service Accounts Enabled
  - Si l'API cible utilise XSRF, implémenter SecureAPIClientWithXSRF
  - Gérer les erreurs 401 avec refresh automatique du token
  - Ajouter du logging pour le debugging

  ---
  10. Points d'attention

  1. SSL en production : Toujours utiliser verify=True en production
  2. Secrets : Ne jamais commiter le client_secret dans le code
  3. Token caching : Le token dure généralement 5 minutes, le réutiliser tant qu'il est valide
  4. XSRF dynamique : Préférer la récupération dynamique du token XSRF plutôt qu'une valeur hard-codée
  5. Refresh token : Le Client Credentials Flow ne fournit pas de refresh token exploitable - simplement redemander un nouveau token
