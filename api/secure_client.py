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
