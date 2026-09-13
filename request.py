import os
import httpx

GITHUB_USERNAME = "samattashbulatov726-ai"
OUTPUT_DIR = "data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

client = httpx.Client(trust_env=False)

repos_response = client.get(f"https://api.github.com/users/{GITHUB_USERNAME}/repos")
repos = repos_response.json()

for repo in repos:
    repo_name = repo["name"]
    default_branch = repo["default_branch"]
    try:
        readme_response = client.get(f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{repo_name}/{default_branch}/README.md")
        if readme_response.status_code == 200:
            with open(f"{OUTPUT_DIR}/{repo_name}.md", "w",encoding="utf-8") as f:
                f.write(readme_response.text)
            print(f"Сохранён README: {repo_name}")
        else:
            print(f"Нет README у {repo_name} (код: {readme_response.status_code})")
    except Exception as e:
        print(f"Ошибка с {repo_name}: {e}")
