import json
import requests
import urllib3

# Suppress "InsecureRequestWarning" for the internal gateway
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AzureOpenAILLM:
    def __init__(self, api_key, endpoint, deployment, api_version, system_prompt):
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_version = api_version
        self.system_prompt = system_prompt
        
        # Construct the full URL dynamically
        # Format: {base}/openai/deployments/{deployment}/chat/completions?api-version={version}
        self.url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    def generate_response(self, query, context=""):
        """
        Sends the query to the Azure/Walmart Gateway and returns the text response.
        """
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        # --- STRICT SYSTEM PROMPT ---
        system_instruction = (
            "You are Friday, a specialized presentation assistant. "
            "You must answer the user's question using ONLY the provided 'Context' below. "
            "Do not use outside knowledge. "
            "If the answer cannot be found in the Context, you must reply exactly: "
            "'I cannot answer that based on the current presentation overview.' "
            "Keep answers concise (maximum 2 sentences) unless asked for details."
        )

        user_message = f"Context: {context}\n\nQuestion: {query}"

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": query}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }

        try:
            print(f"[*] Friday AI: Thinking about '{query}'...")
            
            # verify=False is critical for the internal gateway
            response = requests.post(
                self.url, 
                headers=headers, 
                json=payload, 
                timeout=10, 
                verify=False
            )
            
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()

        except Exception as e:
            print(f"[!] LLM Error: {e}")
            return "I'm sorry, I couldn't connect to the brain network right now."

# --- Factory Function ---
def get_llm(config_path="llm_config.json"):
    """
    Reads config and returns the configured LLM instance.
    """
    try:
        with open(config_path) as f:
            config = json.load(f)
            
        if config["llm"] == "azure_openai":
            return AzureOpenAILLM(
                api_key=config["api_keys"]["azure_openai"],
                endpoint=config["azure_config"]["endpoint_base"],
                deployment=config["azure_config"]["deployment"],
                api_version=config["azure_config"]["api_version"],
                system_prompt=config["system_prompt"]
            )
        else:
            raise ValueError(f"Unsupported LLM type: {config['llm']}")
            
    except FileNotFoundError:
        print("Error: config.json not found.")
        return None
