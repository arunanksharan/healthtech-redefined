"""
SDK Generator Service
Generates code samples and SDK snippets for multiple languages.
"""

from enum import Enum
from typing import Any, Optional

from ..schemas import (
    CodeSample,
    SDKDocumentation,
    SDKLanguage,
)


class SDKGeneratorService:
    """
    SDK Generator Service providing code samples and documentation
    for TypeScript, Python, Java, and .NET SDKs.
    """

    # Base URL placeholder
    BASE_URL = "https://api.healthtech-prm.com"

    def generate_authentication_samples(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
        language: Optional[SDKLanguage] = None
    ) -> list[CodeSample]:
        """
        Generate OAuth authentication code samples for all or specific language.
        """
        samples = []
        scope_string = " ".join(scopes)

        if language is None or language == SDKLanguage.TYPESCRIPT:
            samples.append(self._generate_typescript_auth(
                client_id, redirect_uri, scope_string
            ))

        if language is None or language == SDKLanguage.PYTHON:
            samples.append(self._generate_python_auth(
                client_id, redirect_uri, scope_string
            ))

        if language is None or language == SDKLanguage.JAVA:
            samples.append(self._generate_java_auth(
                client_id, redirect_uri, scope_string
            ))

        if language is None or language == SDKLanguage.CSHARP:
            samples.append(self._generate_csharp_auth(
                client_id, redirect_uri, scope_string
            ))

        return samples

    def generate_api_call_samples(
        self,
        endpoint: str,
        method: str,
        resource_type: str,
        parameters: Optional[dict[str, Any]] = None,
        request_body: Optional[dict[str, Any]] = None,
        language: Optional[SDKLanguage] = None
    ) -> list[CodeSample]:
        """
        Generate API call code samples for all or specific language.
        """
        samples = []

        if language is None or language == SDKLanguage.TYPESCRIPT:
            samples.append(self._generate_typescript_api_call(
                endpoint, method, resource_type, parameters, request_body
            ))

        if language is None or language == SDKLanguage.PYTHON:
            samples.append(self._generate_python_api_call(
                endpoint, method, resource_type, parameters, request_body
            ))

        if language is None or language == SDKLanguage.JAVA:
            samples.append(self._generate_java_api_call(
                endpoint, method, resource_type, parameters, request_body
            ))

        if language is None or language == SDKLanguage.CSHARP:
            samples.append(self._generate_csharp_api_call(
                endpoint, method, resource_type, parameters, request_body
            ))

        return samples

    def generate_fhir_samples(
        self,
        resource_type: str,
        operation: str,  # read, search, create, update, delete
        resource_id: Optional[str] = None,
        search_params: Optional[dict[str, str]] = None,
        resource_data: Optional[dict[str, Any]] = None,
        language: Optional[SDKLanguage] = None
    ) -> list[CodeSample]:
        """
        Generate FHIR operation code samples.
        """
        samples = []

        if language is None or language == SDKLanguage.TYPESCRIPT:
            samples.append(self._generate_typescript_fhir(
                resource_type, operation, resource_id, search_params, resource_data
            ))

        if language is None or language == SDKLanguage.PYTHON:
            samples.append(self._generate_python_fhir(
                resource_type, operation, resource_id, search_params, resource_data
            ))

        if language is None or language == SDKLanguage.JAVA:
            samples.append(self._generate_java_fhir(
                resource_type, operation, resource_id, search_params, resource_data
            ))

        if language is None or language == SDKLanguage.CSHARP:
            samples.append(self._generate_csharp_fhir(
                resource_type, operation, resource_id, search_params, resource_data
            ))

        return samples

    def generate_webhook_samples(
        self,
        event_types: list[str],
        language: Optional[SDKLanguage] = None
    ) -> list[CodeSample]:
        """
        Generate webhook handling code samples.
        """
        samples = []

        if language is None or language == SDKLanguage.TYPESCRIPT:
            samples.append(self._generate_typescript_webhook(event_types))

        if language is None or language == SDKLanguage.PYTHON:
            samples.append(self._generate_python_webhook(event_types))

        if language is None or language == SDKLanguage.JAVA:
            samples.append(self._generate_java_webhook(event_types))

        if language is None or language == SDKLanguage.CSHARP:
            samples.append(self._generate_csharp_webhook(event_types))

        return samples

    def generate_smart_launch_samples(
        self,
        client_id: str,
        scopes: list[str],
        launch_type: str = "ehr",  # ehr or standalone
        language: Optional[SDKLanguage] = None
    ) -> list[CodeSample]:
        """
        Generate SMART on FHIR launch code samples.
        """
        samples = []
        scope_string = " ".join(scopes)

        if language is None or language == SDKLanguage.TYPESCRIPT:
            samples.append(self._generate_typescript_smart(
                client_id, scope_string, launch_type
            ))

        if language is None or language == SDKLanguage.PYTHON:
            samples.append(self._generate_python_smart(
                client_id, scope_string, launch_type
            ))

        return samples

    def get_sdk_documentation(
        self,
        language: SDKLanguage
    ) -> SDKDocumentation:
        """
        Get SDK documentation for a specific language.
        """
        docs = {
            SDKLanguage.TYPESCRIPT: SDKDocumentation(
                language=SDKLanguage.TYPESCRIPT,
                package_name="@healthtech-prm/sdk",
                version="1.0.0",
                installation="npm install @healthtech-prm/sdk",
                quick_start=self._get_typescript_quickstart(),
                api_reference_url=f"{self.BASE_URL}/docs/sdk/typescript",
                github_url="https://github.com/healthtech-prm/sdk-typescript",
                examples_url=f"{self.BASE_URL}/docs/sdk/typescript/examples"
            ),
            SDKLanguage.PYTHON: SDKDocumentation(
                language=SDKLanguage.PYTHON,
                package_name="healthtech-prm-sdk",
                version="1.0.0",
                installation="pip install healthtech-prm-sdk",
                quick_start=self._get_python_quickstart(),
                api_reference_url=f"{self.BASE_URL}/docs/sdk/python",
                github_url="https://github.com/healthtech-prm/sdk-python",
                examples_url=f"{self.BASE_URL}/docs/sdk/python/examples"
            ),
            SDKLanguage.JAVA: SDKDocumentation(
                language=SDKLanguage.JAVA,
                package_name="com.healthtech.prm:sdk",
                version="1.0.0",
                installation="""<dependency>
    <groupId>com.healthtech.prm</groupId>
    <artifactId>sdk</artifactId>
    <version>1.0.0</version>
</dependency>""",
                quick_start=self._get_java_quickstart(),
                api_reference_url=f"{self.BASE_URL}/docs/sdk/java",
                github_url="https://github.com/healthtech-prm/sdk-java",
                examples_url=f"{self.BASE_URL}/docs/sdk/java/examples"
            ),
            SDKLanguage.CSHARP: SDKDocumentation(
                language=SDKLanguage.CSHARP,
                package_name="HealthTech.PRM.SDK",
                version="1.0.0",
                installation="dotnet add package HealthTech.PRM.SDK",
                quick_start=self._get_csharp_quickstart(),
                api_reference_url=f"{self.BASE_URL}/docs/sdk/csharp",
                github_url="https://github.com/healthtech-prm/sdk-csharp",
                examples_url=f"{self.BASE_URL}/docs/sdk/csharp/examples"
            )
        }

        return docs.get(language)

    # TypeScript generators
    def _generate_typescript_auth(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: str
    ) -> CodeSample:
        code = f'''import {{ PRMClient }} from '@healthtech-prm/sdk';

// Initialize the client
const client = new PRMClient({{
  clientId: '{client_id}',
  redirectUri: '{redirect_uri}',
  scopes: '{scopes}'.split(' '),
}});

// Start OAuth flow
async function authenticate() {{
  // Generate authorization URL
  const authUrl = await client.auth.getAuthorizationUrl({{
    state: crypto.randomUUID(),
    codeChallenge: await client.auth.generateCodeChallenge(),
  }});

  // Redirect user to authUrl
  window.location.href = authUrl;
}}

// Handle callback
async function handleCallback(code: string, state: string) {{
  const tokens = await client.auth.exchangeCode(code);

  // Store tokens securely
  client.setAccessToken(tokens.access_token);

  console.log('Authenticated successfully!');
  return tokens;
}}'''

        return CodeSample(
            language=SDKLanguage.TYPESCRIPT,
            title="OAuth 2.0 Authentication",
            description="Authenticate using OAuth 2.0 with PKCE",
            code=code,
            dependencies=["@healthtech-prm/sdk"]
        )

    def _generate_typescript_api_call(
        self,
        endpoint: str,
        method: str,
        resource_type: str,
        parameters: Optional[dict] = None,
        request_body: Optional[dict] = None
    ) -> CodeSample:
        params_str = ""
        if parameters:
            params_str = f"\n    params: {{{', '.join(f'{k}: "{v}"' for k, v in parameters.items())}}},"

        body_str = ""
        if request_body:
            import json
            body_str = f"\n    body: {json.dumps(request_body, indent=6)},"

        code = f'''import {{ PRMClient }} from '@healthtech-prm/sdk';

const client = new PRMClient({{ accessToken: 'your_access_token' }});

async function {method.lower()}{resource_type}() {{
  const response = await client.request({{
    method: '{method}',
    endpoint: '{endpoint}',{params_str}{body_str}
  }});

  return response.data;
}}

// Usage
const result = await {method.lower()}{resource_type}();
console.log(result);'''

        return CodeSample(
            language=SDKLanguage.TYPESCRIPT,
            title=f"{method} {resource_type}",
            description=f"Make a {method} request to {endpoint}",
            code=code,
            dependencies=["@healthtech-prm/sdk"]
        )

    def _generate_typescript_fhir(
        self,
        resource_type: str,
        operation: str,
        resource_id: Optional[str] = None,
        search_params: Optional[dict] = None,
        resource_data: Optional[dict] = None
    ) -> CodeSample:
        if operation == "read":
            code = f'''import {{ PRMClient }} from '@healthtech-prm/sdk';

const client = new PRMClient({{ accessToken: 'your_access_token' }});

async function get{resource_type}(id: string) {{
  const resource = await client.fhir.read('{resource_type}', id);
  return resource;
}}

// Usage
const {resource_type.lower()} = await get{resource_type}('{resource_id or "123"}');
console.log({resource_type.lower()});'''

        elif operation == "search":
            params_obj = search_params or {"name": "John"}
            code = f'''import {{ PRMClient }} from '@healthtech-prm/sdk';

const client = new PRMClient({{ accessToken: 'your_access_token' }});

async function search{resource_type}s() {{
  const bundle = await client.fhir.search('{resource_type}', {{
    {', '.join(f'{k}: "{v}"' for k, v in params_obj.items())}
  }});

  return bundle.entry?.map(e => e.resource) ?? [];
}}

// Usage
const results = await search{resource_type}s();
console.log(`Found ${{results.length}} {resource_type.lower()}s`);'''

        elif operation == "create":
            code = f'''import {{ PRMClient }} from '@healthtech-prm/sdk';

const client = new PRMClient({{ accessToken: 'your_access_token' }});

async function create{resource_type}(data: {resource_type}) {{
  const resource = await client.fhir.create('{resource_type}', data);
  return resource;
}}

// Usage
const new{resource_type} = await create{resource_type}({{
  resourceType: '{resource_type}',
  // ... resource data
}});
console.log('Created:', new{resource_type}.id);'''

        else:
            code = f"// {operation} operation for {resource_type}"

        return CodeSample(
            language=SDKLanguage.TYPESCRIPT,
            title=f"FHIR {operation.title()} {resource_type}",
            description=f"Perform FHIR {operation} operation on {resource_type}",
            code=code,
            dependencies=["@healthtech-prm/sdk"]
        )

    def _generate_typescript_webhook(self, event_types: list[str]) -> CodeSample:
        events_check = " || ".join(f'event.type === "{e}"' for e in event_types[:3])

        code = f'''import {{ PRMWebhookHandler }} from '@healthtech-prm/sdk';
import express from 'express';

const app = express();
const webhookHandler = new PRMWebhookHandler({{
  secret: process.env.WEBHOOK_SECRET!,
}});

app.post('/webhooks/prm', express.raw({{ type: 'application/json' }}), async (req, res) => {{
  try {{
    const signature = req.headers['x-prm-signature'] as string;
    const event = webhookHandler.verifyAndParse(req.body, signature);

    // Handle specific event types
    if ({events_check}) {{
      console.log('Processing event:', event.type);
      await processEvent(event);
    }}

    res.status(200).json({{ received: true }});
  }} catch (error) {{
    console.error('Webhook error:', error);
    res.status(400).json({{ error: 'Invalid webhook' }});
  }}
}});

async function processEvent(event: PRMWebhookEvent) {{
  switch (event.type) {{
    case '{event_types[0] if event_types else "patient.created"}':
      // Handle event
      break;
    default:
      console.log('Unhandled event type:', event.type);
  }}
}}'''

        return CodeSample(
            language=SDKLanguage.TYPESCRIPT,
            title="Webhook Handler",
            description="Handle incoming webhooks with signature verification",
            code=code,
            dependencies=["@healthtech-prm/sdk", "express"]
        )

    def _generate_typescript_smart(
        self,
        client_id: str,
        scopes: str,
        launch_type: str
    ) -> CodeSample:
        code = f'''import {{ SMARTClient }} from '@healthtech-prm/sdk';

// Initialize SMART client
const smart = new SMARTClient({{
  clientId: '{client_id}',
  scopes: '{scopes}'.split(' '),
  redirectUri: window.location.origin + '/callback',
}});

// {'EHR' if launch_type == 'ehr' else 'Standalone'} Launch
async function launch() {{
  {'// Get launch context from EHR' if launch_type == 'ehr' else '// Standalone launch'}
  const launchParams = {{"iss": await smart.getFhirServerUrl(){'", launch": getLaunchToken()' if launch_type == 'ehr' else ''}}};

  // Authorize
  await smart.authorize(launchParams);
}}

// Handle authorization callback
async function handleCallback() {{
  const client = await smart.completeAuthorization();

  // Get patient context
  const patient = await client.patient.read();
  console.log('Current patient:', patient.name);

  // Access FHIR data with context
  const observations = await client.patient.search('Observation', {{
    category: 'vital-signs',
    _sort: '-date',
    _count: 10
  }});

  return {{ patient, observations }};
}}'''

        return CodeSample(
            language=SDKLanguage.TYPESCRIPT,
            title=f"SMART on FHIR {launch_type.upper()} Launch",
            description=f"Implement SMART on FHIR {launch_type} launch flow",
            code=code,
            dependencies=["@healthtech-prm/sdk"]
        )

    # Python generators
    def _generate_python_auth(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: str
    ) -> CodeSample:
        code = f'''from healthtech_prm_sdk import PRMClient
import secrets

# Initialize the client
client = PRMClient(
    client_id="{client_id}",
    redirect_uri="{redirect_uri}",
    scopes="{scopes}".split(),
)

# Generate authorization URL
def get_auth_url():
    state = secrets.token_urlsafe(32)
    code_verifier = client.auth.generate_code_verifier()

    auth_url = client.auth.get_authorization_url(
        state=state,
        code_verifier=code_verifier,
    )

    # Store state and code_verifier in session
    return auth_url, state, code_verifier

# Handle callback
async def handle_callback(code: str, code_verifier: str):
    tokens = await client.auth.exchange_code(
        code=code,
        code_verifier=code_verifier,
    )

    # Store tokens securely
    client.set_access_token(tokens.access_token)

    print("Authenticated successfully!")
    return tokens'''

        return CodeSample(
            language=SDKLanguage.PYTHON,
            title="OAuth 2.0 Authentication",
            description="Authenticate using OAuth 2.0 with PKCE",
            code=code,
            dependencies=["healthtech-prm-sdk"]
        )

    def _generate_python_api_call(
        self,
        endpoint: str,
        method: str,
        resource_type: str,
        parameters: Optional[dict] = None,
        request_body: Optional[dict] = None
    ) -> CodeSample:
        params_str = ""
        if parameters:
            params_str = f"\n        params={parameters},"

        body_str = ""
        if request_body:
            body_str = f"\n        json={request_body},"

        code = f'''from healthtech_prm_sdk import PRMClient

client = PRMClient(access_token="your_access_token")

async def {method.lower()}_{resource_type.lower()}():
    response = await client.request(
        method="{method}",
        endpoint="{endpoint}",{params_str}{body_str}
    )

    return response.data

# Usage
result = await {method.lower()}_{resource_type.lower()}()
print(result)'''

        return CodeSample(
            language=SDKLanguage.PYTHON,
            title=f"{method} {resource_type}",
            description=f"Make a {method} request to {endpoint}",
            code=code,
            dependencies=["healthtech-prm-sdk"]
        )

    def _generate_python_fhir(
        self,
        resource_type: str,
        operation: str,
        resource_id: Optional[str] = None,
        search_params: Optional[dict] = None,
        resource_data: Optional[dict] = None
    ) -> CodeSample:
        if operation == "read":
            code = f'''from healthtech_prm_sdk import PRMClient

client = PRMClient(access_token="your_access_token")

async def get_{resource_type.lower()}(resource_id: str):
    resource = await client.fhir.read("{resource_type}", resource_id)
    return resource

# Usage
{resource_type.lower()} = await get_{resource_type.lower()}("{resource_id or '123'}")
print({resource_type.lower()})'''

        elif operation == "search":
            params_obj = search_params or {"name": "John"}
            code = f'''from healthtech_prm_sdk import PRMClient

client = PRMClient(access_token="your_access_token")

async def search_{resource_type.lower()}s():
    bundle = await client.fhir.search(
        "{resource_type}",
        {params_obj}
    )

    return [entry.resource for entry in bundle.entry or []]

# Usage
results = await search_{resource_type.lower()}s()
print(f"Found {{len(results)}} {resource_type.lower()}s")'''

        elif operation == "create":
            code = f'''from healthtech_prm_sdk import PRMClient

client = PRMClient(access_token="your_access_token")

async def create_{resource_type.lower()}(data: dict):
    resource = await client.fhir.create("{resource_type}", data)
    return resource

# Usage
new_{resource_type.lower()} = await create_{resource_type.lower()}({{
    "resourceType": "{resource_type}",
    # ... resource data
}})
print(f"Created: {{new_{resource_type.lower()}.id}}")'''

        else:
            code = f"# {operation} operation for {resource_type}"

        return CodeSample(
            language=SDKLanguage.PYTHON,
            title=f"FHIR {operation.title()} {resource_type}",
            description=f"Perform FHIR {operation} operation on {resource_type}",
            code=code,
            dependencies=["healthtech-prm-sdk"]
        )

    def _generate_python_webhook(self, event_types: list[str]) -> CodeSample:
        code = f'''from fastapi import FastAPI, Request, HTTPException
from healthtech_prm_sdk import PRMWebhookHandler
import os

app = FastAPI()
webhook_handler = PRMWebhookHandler(secret=os.environ["WEBHOOK_SECRET"])

@app.post("/webhooks/prm")
async def handle_webhook(request: Request):
    signature = request.headers.get("x-prm-signature")
    body = await request.body()

    try:
        event = webhook_handler.verify_and_parse(body, signature)

        # Handle specific event types
        if event.type in {event_types}:
            await process_event(event)

        return {{"received": True}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def process_event(event):
    match event.type:
        case "{event_types[0] if event_types else 'patient.created'}":
            # Handle event
            pass
        case _:
            print(f"Unhandled event type: {{event.type}}")'''

        return CodeSample(
            language=SDKLanguage.PYTHON,
            title="Webhook Handler",
            description="Handle incoming webhooks with signature verification",
            code=code,
            dependencies=["healthtech-prm-sdk", "fastapi"]
        )

    def _generate_python_smart(
        self,
        client_id: str,
        scopes: str,
        launch_type: str
    ) -> CodeSample:
        code = f'''from healthtech_prm_sdk import SMARTClient

# Initialize SMART client
smart = SMARTClient(
    client_id="{client_id}",
    scopes="{scopes}".split(),
    redirect_uri="http://localhost:8000/callback",
)

# {'EHR' if launch_type == 'ehr' else 'Standalone'} Launch
async def launch(iss: str{', launch_token: str' if launch_type == 'ehr' else ''}):
    auth_url = await smart.authorize(
        iss=iss,
        {'launch=launch_token,' if launch_type == 'ehr' else ''}
    )
    return auth_url

# Handle authorization callback
async def handle_callback(code: str, state: str):
    client = await smart.complete_authorization(code, state)

    # Get patient context
    patient = await client.patient.read()
    print(f"Current patient: {{patient.name}}")

    # Access FHIR data with context
    observations = await client.patient.search(
        "Observation",
        category="vital-signs",
        _sort="-date",
        _count=10
    )

    return patient, observations'''

        return CodeSample(
            language=SDKLanguage.PYTHON,
            title=f"SMART on FHIR {launch_type.upper()} Launch",
            description=f"Implement SMART on FHIR {launch_type} launch flow",
            code=code,
            dependencies=["healthtech-prm-sdk"]
        )

    # Java generators
    def _generate_java_auth(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: str
    ) -> CodeSample:
        code = f'''import com.healthtech.prm.PRMClient;
import com.healthtech.prm.auth.OAuth2Config;
import com.healthtech.prm.auth.TokenResponse;
import java.util.Arrays;
import java.util.UUID;

public class AuthExample {{
    private final PRMClient client;

    public AuthExample() {{
        OAuth2Config config = OAuth2Config.builder()
            .clientId("{client_id}")
            .redirectUri("{redirect_uri}")
            .scopes(Arrays.asList("{scopes}".split(" ")))
            .build();

        this.client = new PRMClient(config);
    }}

    public String getAuthorizationUrl() {{
        String state = UUID.randomUUID().toString();
        String codeVerifier = client.getAuth().generateCodeVerifier();

        // Store state and codeVerifier in session
        return client.getAuth().getAuthorizationUrl(state, codeVerifier);
    }}

    public TokenResponse handleCallback(String code, String codeVerifier) {{
        TokenResponse tokens = client.getAuth().exchangeCode(code, codeVerifier);

        client.setAccessToken(tokens.getAccessToken());
        System.out.println("Authenticated successfully!");

        return tokens;
    }}
}}'''

        return CodeSample(
            language=SDKLanguage.JAVA,
            title="OAuth 2.0 Authentication",
            description="Authenticate using OAuth 2.0 with PKCE",
            code=code,
            dependencies=["com.healthtech.prm:sdk:1.0.0"]
        )

    def _generate_java_api_call(
        self,
        endpoint: str,
        method: str,
        resource_type: str,
        parameters: Optional[dict] = None,
        request_body: Optional[dict] = None
    ) -> CodeSample:
        code = f'''import com.healthtech.prm.PRMClient;
import com.healthtech.prm.http.ApiResponse;
import java.util.Map;

public class ApiCallExample {{
    private final PRMClient client;

    public ApiCallExample(String accessToken) {{
        this.client = PRMClient.withAccessToken(accessToken);
    }}

    public ApiResponse {method.lower()}{resource_type}() throws Exception {{
        return client.request()
            .method("{method}")
            .endpoint("{endpoint}")
            .execute();
    }}

    public static void main(String[] args) throws Exception {{
        ApiCallExample example = new ApiCallExample("your_access_token");
        ApiResponse result = example.{method.lower()}{resource_type}();
        System.out.println(result.getData());
    }}
}}'''

        return CodeSample(
            language=SDKLanguage.JAVA,
            title=f"{method} {resource_type}",
            description=f"Make a {method} request to {endpoint}",
            code=code,
            dependencies=["com.healthtech.prm:sdk:1.0.0"]
        )

    def _generate_java_fhir(
        self,
        resource_type: str,
        operation: str,
        resource_id: Optional[str] = None,
        search_params: Optional[dict] = None,
        resource_data: Optional[dict] = None
    ) -> CodeSample:
        if operation == "read":
            code = f'''import com.healthtech.prm.PRMClient;
import com.healthtech.prm.fhir.{resource_type};

public class FhirReadExample {{
    private final PRMClient client;

    public FhirReadExample(String accessToken) {{
        this.client = PRMClient.withAccessToken(accessToken);
    }}

    public {resource_type} get{resource_type}(String id) {{
        return client.fhir().read({resource_type}.class, id);
    }}

    public static void main(String[] args) {{
        FhirReadExample example = new FhirReadExample("your_access_token");
        {resource_type} resource = example.get{resource_type}("{resource_id or '123'}");
        System.out.println(resource);
    }}
}}'''
        elif operation == "search":
            code = f'''import com.healthtech.prm.PRMClient;
import com.healthtech.prm.fhir.{resource_type};
import com.healthtech.prm.fhir.Bundle;
import java.util.List;

public class FhirSearchExample {{
    private final PRMClient client;

    public FhirSearchExample(String accessToken) {{
        this.client = PRMClient.withAccessToken(accessToken);
    }}

    public List<{resource_type}> search{resource_type}s() {{
        Bundle bundle = client.fhir().search({resource_type}.class)
            .where("name", "John")
            .execute();

        return bundle.getEntryResources({resource_type}.class);
    }}
}}'''
        else:
            code = f"// {operation} operation for {resource_type}"

        return CodeSample(
            language=SDKLanguage.JAVA,
            title=f"FHIR {operation.title()} {resource_type}",
            description=f"Perform FHIR {operation} operation on {resource_type}",
            code=code,
            dependencies=["com.healthtech.prm:sdk:1.0.0"]
        )

    def _generate_java_webhook(self, event_types: list[str]) -> CodeSample:
        code = f'''import com.healthtech.prm.webhook.PRMWebhookHandler;
import com.healthtech.prm.webhook.WebhookEvent;
import org.springframework.web.bind.annotation.*;

@RestController
public class WebhookController {{
    private final PRMWebhookHandler webhookHandler;

    public WebhookController() {{
        this.webhookHandler = new PRMWebhookHandler(System.getenv("WEBHOOK_SECRET"));
    }}

    @PostMapping("/webhooks/prm")
    public Map<String, Boolean> handleWebhook(
        @RequestBody String body,
        @RequestHeader("x-prm-signature") String signature
    ) {{
        try {{
            WebhookEvent event = webhookHandler.verifyAndParse(body, signature);

            switch (event.getType()) {{
                case "{event_types[0] if event_types else 'patient.created'}":
                    processEvent(event);
                    break;
                default:
                    System.out.println("Unhandled event type: " + event.getType());
            }}

            return Map.of("received", true);
        }} catch (Exception e) {{
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, e.getMessage());
        }}
    }}

    private void processEvent(WebhookEvent event) {{
        // Handle the event
    }}
}}'''

        return CodeSample(
            language=SDKLanguage.JAVA,
            title="Webhook Handler",
            description="Handle incoming webhooks with signature verification",
            code=code,
            dependencies=["com.healthtech.prm:sdk:1.0.0", "spring-boot-starter-web"]
        )

    # C# generators
    def _generate_csharp_auth(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: str
    ) -> CodeSample:
        code = f'''using HealthTech.PRM.SDK;
using HealthTech.PRM.SDK.Auth;

public class AuthExample
{{
    private readonly PRMClient _client;

    public AuthExample()
    {{
        var config = new OAuth2Config
        {{
            ClientId = "{client_id}",
            RedirectUri = "{redirect_uri}",
            Scopes = "{scopes}".Split(' ')
        }};

        _client = new PRMClient(config);
    }}

    public string GetAuthorizationUrl()
    {{
        var state = Guid.NewGuid().ToString();
        var codeVerifier = _client.Auth.GenerateCodeVerifier();

        // Store state and codeVerifier in session
        return _client.Auth.GetAuthorizationUrl(state, codeVerifier);
    }}

    public async Task<TokenResponse> HandleCallbackAsync(string code, string codeVerifier)
    {{
        var tokens = await _client.Auth.ExchangeCodeAsync(code, codeVerifier);

        _client.SetAccessToken(tokens.AccessToken);
        Console.WriteLine("Authenticated successfully!");

        return tokens;
    }}
}}'''

        return CodeSample(
            language=SDKLanguage.CSHARP,
            title="OAuth 2.0 Authentication",
            description="Authenticate using OAuth 2.0 with PKCE",
            code=code,
            dependencies=["HealthTech.PRM.SDK"]
        )

    def _generate_csharp_api_call(
        self,
        endpoint: str,
        method: str,
        resource_type: str,
        parameters: Optional[dict] = None,
        request_body: Optional[dict] = None
    ) -> CodeSample:
        code = f'''using HealthTech.PRM.SDK;
using HealthTech.PRM.SDK.Http;

public class ApiCallExample
{{
    private readonly PRMClient _client;

    public ApiCallExample(string accessToken)
    {{
        _client = PRMClient.WithAccessToken(accessToken);
    }}

    public async Task<ApiResponse> {method.title()}{resource_type}Async()
    {{
        return await _client.RequestAsync(new RequestOptions
        {{
            Method = "{method}",
            Endpoint = "{endpoint}"
        }});
    }}

    public static async Task Main(string[] args)
    {{
        var example = new ApiCallExample("your_access_token");
        var result = await example.{method.title()}{resource_type}Async();
        Console.WriteLine(result.Data);
    }}
}}'''

        return CodeSample(
            language=SDKLanguage.CSHARP,
            title=f"{method} {resource_type}",
            description=f"Make a {method} request to {endpoint}",
            code=code,
            dependencies=["HealthTech.PRM.SDK"]
        )

    def _generate_csharp_fhir(
        self,
        resource_type: str,
        operation: str,
        resource_id: Optional[str] = None,
        search_params: Optional[dict] = None,
        resource_data: Optional[dict] = None
    ) -> CodeSample:
        if operation == "read":
            code = f'''using HealthTech.PRM.SDK;
using HealthTech.PRM.SDK.Fhir;

public class FhirReadExample
{{
    private readonly PRMClient _client;

    public FhirReadExample(string accessToken)
    {{
        _client = PRMClient.WithAccessToken(accessToken);
    }}

    public async Task<{resource_type}> Get{resource_type}Async(string id)
    {{
        return await _client.Fhir.ReadAsync<{resource_type}>(id);
    }}

    public static async Task Main(string[] args)
    {{
        var example = new FhirReadExample("your_access_token");
        var resource = await example.Get{resource_type}Async("{resource_id or '123'}");
        Console.WriteLine(resource);
    }}
}}'''
        elif operation == "search":
            code = f'''using HealthTech.PRM.SDK;
using HealthTech.PRM.SDK.Fhir;

public class FhirSearchExample
{{
    private readonly PRMClient _client;

    public FhirSearchExample(string accessToken)
    {{
        _client = PRMClient.WithAccessToken(accessToken);
    }}

    public async Task<List<{resource_type}>> Search{resource_type}sAsync()
    {{
        var bundle = await _client.Fhir.SearchAsync<{resource_type}>(
            new SearchParams {{ ["name"] = "John" }}
        );

        return bundle.Entry.Select(e => e.Resource).Cast<{resource_type}>().ToList();
    }}
}}'''
        else:
            code = f"// {operation} operation for {resource_type}"

        return CodeSample(
            language=SDKLanguage.CSHARP,
            title=f"FHIR {operation.title()} {resource_type}",
            description=f"Perform FHIR {operation} operation on {resource_type}",
            code=code,
            dependencies=["HealthTech.PRM.SDK"]
        )

    def _generate_csharp_webhook(self, event_types: list[str]) -> CodeSample:
        code = f'''using HealthTech.PRM.SDK.Webhook;
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("webhooks")]
public class WebhookController : ControllerBase
{{
    private readonly PRMWebhookHandler _webhookHandler;

    public WebhookController()
    {{
        _webhookHandler = new PRMWebhookHandler(Environment.GetEnvironmentVariable("WEBHOOK_SECRET"));
    }}

    [HttpPost("prm")]
    public async Task<IActionResult> HandleWebhook(
        [FromBody] string body,
        [FromHeader(Name = "x-prm-signature")] string signature)
    {{
        try
        {{
            var webhookEvent = _webhookHandler.VerifyAndParse(body, signature);

            switch (webhookEvent.Type)
            {{
                case "{event_types[0] if event_types else 'patient.created'}":
                    await ProcessEventAsync(webhookEvent);
                    break;
                default:
                    Console.WriteLine($"Unhandled event type: {{webhookEvent.Type}}");
                    break;
            }}

            return Ok(new {{ received = true }});
        }}
        catch (Exception ex)
        {{
            return BadRequest(ex.Message);
        }}
    }}

    private async Task ProcessEventAsync(WebhookEvent webhookEvent)
    {{
        // Handle the event
    }}
}}'''

        return CodeSample(
            language=SDKLanguage.CSHARP,
            title="Webhook Handler",
            description="Handle incoming webhooks with signature verification",
            code=code,
            dependencies=["HealthTech.PRM.SDK", "Microsoft.AspNetCore"]
        )

    # Quick start guides
    def _get_typescript_quickstart(self) -> str:
        return '''// 1. Install the SDK
// npm install @healthtech-prm/sdk

// 2. Initialize the client
import { PRMClient } from '@healthtech-prm/sdk';

const client = new PRMClient({
  clientId: 'your_client_id',
  redirectUri: 'http://localhost:3000/callback',
});

// 3. Authenticate
await client.auth.login();

// 4. Make API calls
const patients = await client.fhir.search('Patient', { name: 'John' });
console.log(patients);'''

    def _get_python_quickstart(self) -> str:
        return '''# 1. Install the SDK
# pip install healthtech-prm-sdk

# 2. Initialize the client
from healthtech_prm_sdk import PRMClient

client = PRMClient(
    client_id="your_client_id",
    redirect_uri="http://localhost:8000/callback",
)

# 3. Authenticate
await client.auth.login()

# 4. Make API calls
patients = await client.fhir.search("Patient", name="John")
print(patients)'''

    def _get_java_quickstart(self) -> str:
        return '''// 1. Add dependency
// Maven: com.healthtech.prm:sdk:1.0.0

// 2. Initialize the client
import com.healthtech.prm.PRMClient;

PRMClient client = PRMClient.builder()
    .clientId("your_client_id")
    .redirectUri("http://localhost:8080/callback")
    .build();

// 3. Authenticate
client.getAuth().login();

// 4. Make API calls
Bundle patients = client.fhir().search(Patient.class)
    .where("name", "John")
    .execute();
System.out.println(patients);'''

    def _get_csharp_quickstart(self) -> str:
        return '''// 1. Install the SDK
// dotnet add package HealthTech.PRM.SDK

// 2. Initialize the client
using HealthTech.PRM.SDK;

var client = new PRMClient(new ClientConfig
{
    ClientId = "your_client_id",
    RedirectUri = "http://localhost:5000/callback"
});

// 3. Authenticate
await client.Auth.LoginAsync();

// 4. Make API calls
var patients = await client.Fhir.SearchAsync<Patient>(
    new SearchParams { ["name"] = "John" }
);
Console.WriteLine(patients);'''
