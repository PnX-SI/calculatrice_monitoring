import os
import sys

import requests

# Configuration
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = os.environ["OWNER"]
REPO = os.environ["REPO"]
COMPLEXITY_FIELD_ID = os.environ["COMPLEXITY_FIELD_ID"]
EPIC_COMPLEXITY_FIELD_ID = os.environ["EPIC_COMPLEXITY_FIELD_ID"]
PROJECT_ID = os.environ["PROJECT_ID"]

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
graphql_headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def update_epic_complexity(issue, complexity_value):
    """Met à jour la valeur du champ complexité d'une issue

    Args:
        issue: Objet issue récupéré via l'API REST GitHub
        complexity_value: Valeur numérique de la complexité
    """
    issue_number = issue.get("number")
    node_id = issue.get("node_id")

    print(f"\n🔄 Mise à jour complexité issue #{issue_number} -> {complexity_value}")

    if not node_id:
        print(f"❌ Pas de node_id pour l'issue #{issue_number}")
        return False

    # 1. Trouver l'item du projet pour cette issue
    project_item_id = get_project_item_id(node_id)
    if not project_item_id:
        print(f"❌ Issue #{issue_number} non trouvée dans le projet {PROJECT_ID}")
        return False

    # 2. Mettre à jour le champ complexité
    graphql_url = "https://api.github.com/graphql"

    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: Float!) {
        updateProjectV2ItemFieldValue(
            input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: {
                    number: $value
                }
            }
        ) {
            projectV2Item {
                id
                fieldValues(first: 1) {
                    nodes {
                        ... on ProjectV2ItemFieldNumberValue {
                            field {
                                ... on ProjectV2Field {
                                    name
                                }
                            }
                            number
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "projectId": PROJECT_ID,
        "itemId": project_item_id,
        "fieldId": EPIC_COMPLEXITY_FIELD_ID,
        "value": float(complexity_value),
    }

    response = requests.post(
        graphql_url,
        json={"query": mutation, "variables": variables},
        headers=graphql_headers,
    )

    if response.status_code != 200:
        print(f"❌ Erreur GraphQL: {response.status_code}")
        print(f"Réponse: {response.text}")
        return False

    data = response.json()

    if "errors" in data:
        print(f"❌ Erreurs GraphQL: {data['errors']}")
        return False

    update_result = data.get("data", {}).get("updateProjectV2ItemFieldValue")
    if update_result:
        print(f"✅ Complexité mise à jour pour issue #{issue_number}: {complexity_value}")
        return True
    else:
        print(f"❌ Échec de la mise à jour pour issue #{issue_number}")
        print(f"Réponse: {data}")
        return False


def get_project_item_id(issue_node_id):
    """Récupère l'ID de l'item du projet pour une issue"""
    print(f"🔍 Recherche project item ID pour node: {issue_node_id}")

    graphql_url = "https://api.github.com/graphql"

    query = """
    query($nodeId: ID!) {
        node(id: $nodeId) {
            ... on Issue {
                number
                projectItems(first: 10) {
                    nodes {
                        id
                        project {
                            id
                        }
                    }
                }
            }
        }
    }
    """

    response = requests.post(
        graphql_url,
        json={"query": query, "variables": {"nodeId": issue_node_id}},
        headers=graphql_headers,
    )

    if response.status_code != 200:
        print(f"❌ Erreur GraphQL: {response.status_code}")
        return None

    data = response.json()

    if "errors" in data:
        print(f"❌ Erreurs GraphQL: {data['errors']}")
        return None

    try:
        node_data = data.get("data", {}).get("node")
        if not node_data:
            return None

        project_items = node_data.get("projectItems", {}).get("nodes", [])

        # Chercher l'item correspondant au bon projet
        for item in project_items:
            if not item:
                continue

            project = item.get("project", {})
            if project.get("id") == PROJECT_ID:
                item_id = item.get("id")
                print(f"✅ Project item ID trouvé: {item_id}")
                return item_id

        print(f"❌ Aucun item trouvé pour le projet {PROJECT_ID}")
        return None

    except (KeyError, TypeError) as e:
        print(f"❌ Erreur lors du parsing: {e}")
        return None


def get_issue_complexity(issue):
    """Récupère la valeur du champ complexité d'une issue"""
    issue_number = issue.get("number")
    issue_node_id = issue.get("node_id")

    print(f"🔍 Recherche complexité pour issue #{issue_number} (node_id: {issue_node_id})")

    if not issue_node_id:
        print(f"❌ Pas de node_id pour l'issue #{issue_number}")
        return None

    # Requête GraphQL utilisant l'ID du champ directement
    graphql_url = "https://api.github.com/graphql"

    query = """
    query($nodeId: ID!) {
        node(id: $nodeId) {
            ... on Issue {
                number
                title
                projectItems(first: 10) {
                    nodes {
                        id
                        project {
                            id
                            title
                        }
                        fieldValues(first: 20) {
                            nodes {
                                ... on ProjectV2ItemFieldSingleSelectValue {
                                    field {
                                        ... on ProjectV2SingleSelectField {
                                            id
                                            name
                                        }
                                    }
                                    name
                                }
                                ... on ProjectV2ItemFieldNumberValue {
                                    field {
                                        ... on ProjectV2Field {
                                            id
                                            name
                                        }
                                    }
                                    number
                                }
                                ... on ProjectV2ItemFieldTextValue {
                                    field {
                                        ... on ProjectV2Field {
                                            id
                                            name
                                        }
                                    }
                                    text
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    response = requests.post(
        graphql_url,
        json={"query": query, "variables": {"nodeId": issue_node_id}},
        headers=graphql_headers,
    )

    if response.status_code != 200:
        print(f"❌ Erreur GraphQL pour l'issue #{issue_number}")
        print(f"Status: {response.status_code}")
        print(f"Réponse: {response.text}")
        return None

    data = response.json()

    try:
        node_data = data.get("data", {}).get("node")
        if not node_data:
            print(f"❌ Aucune donnée pour le node {issue_node_id}")
            return None

        project_items = node_data.get("projectItems", {}).get("nodes", [])
        if not project_items:
            print(f"⚠️ L'issue #{issue_number} n'est liée à aucun projet")
            return None

        print(f"📊 Issue #{issue_number} trouvée dans {len(project_items)} projet(s)")

        for item in project_items:
            if not item:  # Vérification de sécurité
                continue

            project_info = item.get("project", {})
            print(f"  Projet: {project_info.get('title')} (ID: {project_info.get('id')})")

            # Vérifier si c'est le bon projet
            if project_info.get("id") == PROJECT_ID:
                print("✅ Projet correspondant trouvé!")

                field_values = item.get("fieldValues", {}).get("nodes", [])
                for field_value in field_values:
                    if not field_value:
                        continue

                    field_info = field_value.get("field", {})
                    field_id = field_info.get("id")
                    if field_id == COMPLEXITY_FIELD_ID:
                        return field_value["number"]

        print(
            f"❌ Champ complexité (ID: {COMPLEXITY_FIELD_ID})"
            + f" non trouvé pour l'issue #{issue_number}"
        )
        return None

    except (KeyError, TypeError) as e:
        print(f"❌ Erreur lors du parsing: {e}")
        return None


def get_sub_issues(issue_number):
    """Récupère directement les sub-issues via l'endpoint dédié"""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{issue_number}/sub_issues"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print("❌ Erreur lors de la récupération des sub-issues")
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.text}")
    return []


def get_issue(issue_number):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{issue_number}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print("❌ Erreur lors de la récupération des sub-issues")
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.text}")
    return []


def get_parent_issue(issue):
    issue_node_id = issue.get("node_id")
    query = """
        query($issueId: ID!) {
          node(id: $issueId) {
            ... on Issue {
              parent {
                number
                title
                url
              }
              subIssues(first: 10) {
                nodes {
                  number
                  title
                  url
                }
              }
            }
          }
        }
    """

    variables = {"issueId": issue_node_id}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
    )

    data = response.json()
    return data["data"]["node"]["parent"]


def update_complexity(issue_number):
    print("\n=== Début de la mise à jour de la complexité de l'epic ===")

    # Récupérer les sub-issues
    print(f"\n📑 Recherche des sub-issues pour l'epic #{issue_number}...")
    sub_issues = get_sub_issues(issue_number)

    if not sub_issues:
        print("ℹ️ Aucune sub-issue trouvée pour cet epic")
    else:
        print(f"\nNombre de sub-issues trouvées : {len(sub_issues)}: {sub_issues}")
        epic_complexity = 0
        for issue in sub_issues:
            if issue_complexity := get_issue_complexity(issue):
                print(f"adding issue {issue['title']} {issue_complexity}")
                epic_complexity += issue_complexity
        update_epic_complexity(get_issue(issue_number), epic_complexity)
    if parent := get_parent_issue(get_issue(issue_number)):
        update_complexity(parent["number"])


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_epic_complexity.py <issue_number>")
        sys.exit(1)
    issue_number = sys.argv[1]
    update_complexity(issue_number)


if __name__ == "__main__":
    main()
