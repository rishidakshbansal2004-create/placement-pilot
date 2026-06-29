"""
Placement Pilot — setup_permissions.py
Sets up all agent and function permissions after setup_pod.py runs.
Also creates the /resumes folder for resume PDF storage.
Run: python setup_permissions.py
"""

import os
import sys
from dotenv import load_dotenv
from lemma_sdk import Pod, LemmaAPIError
from lemma_sdk.openapi_client.models.agent_permissions_replace_request import AgentPermissionsReplaceRequest
from lemma_sdk.openapi_client.models.agent_resource_permission_request import AgentResourcePermissionRequest
from lemma_sdk.openapi_client.models.function_permissions_replace_request import FunctionPermissionsReplaceRequest
from lemma_sdk.openapi_client.models.function_resource_permission_request import FunctionResourcePermissionRequest
from lemma_sdk.openapi_client.models.resource_type import ResourceType

load_dotenv()

# ── Permission helpers ─────────────────────────────────────────────────────────

TABLE_READ  = ["datastore.record.read", "datastore.table.read"]
TABLE_WRITE = ["datastore.record.read", "datastore.record.write", "datastore.table.read"]
AGENT_PERMS = ["agent.read", "agent.execute"]
FN_PERMS    = ["function.read", "function.execute"]


def agent_grant(resource_name, resource_type, permission_ids):
    return AgentResourcePermissionRequest(
        resource_name=resource_name,
        resource_type=ResourceType(resource_type),
        permission_ids=permission_ids,
    )


def fn_grant(resource_name, resource_type, permission_ids):
    return FunctionResourcePermissionRequest(
        resource_name=resource_name,
        resource_type=ResourceType(resource_type),
        permission_ids=permission_ids,
    )


# ── Folder setup ───────────────────────────────────────────────────────────────

def setup_folders(pod):
    print("\n📁 Setting up folders...")
    try:
        pod.files.create_folder("/resumes", description="User resume PDFs — accessible by resume_parser agent")
        print("  ✅ Created /resumes folder")
    except Exception as e:
        print(f"  ⏭  /resumes folder may already exist")

    # Move any resumes uploaded to root into /resumes/
    try:
        files = pod.files.list("/")
        files_d = files.to_dict() if hasattr(files, "to_dict") else files
        items = files_d.get("items", []) if isinstance(files_d, dict) else []
        for item in items:
            name = item.get("name", "") if isinstance(item, dict) else ""
            path = item.get("path", "") if isinstance(item, dict) else ""
            if name.endswith(".pdf") and path and not path.startswith("/resumes/"):
                new_path = f"/resumes/{name}"
                try:
                    pod.files.move(path, new_path)
                    print(f"  ✅ Moved {path} → {new_path}")
                except Exception as move_err:
                    print(f"  ⏭  Could not move {path}: {move_err}")
    except Exception as e:
        print(f"  ⚠️  Could not list root files: {e}")


# ── Agent permissions ──────────────────────────────────────────────────────────

def setup_agent_permissions(pod):
    print("\n🔐 Setting agent permissions...")

    # placement_runner — orchestrator, needs everything
    pod.agents.replace_permissions("placement_runner", AgentPermissionsReplaceRequest(
        grants=[
            agent_grant("resumes",           "datastore_table", TABLE_READ),
            agent_grant("job_postings",      "datastore_table", TABLE_READ),
            agent_grant("job_matches",       "datastore_table", TABLE_WRITE),
            agent_grant("outreach_messages", "datastore_table", TABLE_READ),
            agent_grant("user_profiles",     "datastore_table", TABLE_READ),
            agent_grant("job_hunter",        "agent",           AGENT_PERMS),
            agent_grant("resume_parser",     "agent",           AGENT_PERMS),
            agent_grant("outreach_composer", "agent",           AGENT_PERMS),
            agent_grant("score_match",       "function",        FN_PERMS),
        ]
    ))
    print("  ✅ placement_runner")

    # job_hunter — searches web, writes job_postings, reads user_profiles
    pod.agents.replace_permissions("job_hunter", AgentPermissionsReplaceRequest(
        grants=[
            agent_grant("job_postings",  "datastore_table", TABLE_WRITE),
            agent_grant("resumes",       "datastore_table", TABLE_READ),
            agent_grant("user_profiles", "datastore_table", TABLE_READ),
        ]
    ))
    print("  ✅ job_hunter")

    # resume_parser — writes resumes table (file access via WORKSPACE_CLI toolset)
    pod.agents.replace_permissions("resume_parser", AgentPermissionsReplaceRequest(
        grants=[
            agent_grant("resumes", "datastore_table", TABLE_WRITE),
        ]
    ))
    print("  ✅ resume_parser")

    # outreach_composer — reads everything, writes outreach_messages, calls send_telegram
    pod.agents.replace_permissions("outreach_composer", AgentPermissionsReplaceRequest(
        grants=[
            agent_grant("job_matches",       "datastore_table", TABLE_READ),
            agent_grant("job_postings",      "datastore_table", TABLE_READ),
            agent_grant("resumes",           "datastore_table", TABLE_READ),
            agent_grant("outreach_messages", "datastore_table", TABLE_WRITE),
            agent_grant("user_profiles",     "datastore_table", TABLE_READ),
            agent_grant("send_telegram",     "function",        FN_PERMS),
        ]
    ))
    print("  ✅ outreach_composer")


# ── Function permissions ───────────────────────────────────────────────────────

def setup_function_permissions(pod):
    print("\n⚙️  Setting function permissions...")

    # score_match — reads job_postings + resumes, writes job_matches
    pod.functions.replace_permissions("score_match", FunctionPermissionsReplaceRequest(
        grants=[
            fn_grant("job_postings", "datastore_table", TABLE_READ),
            fn_grant("resumes",      "datastore_table", TABLE_READ),
            fn_grant("job_matches",  "datastore_table", TABLE_WRITE),
        ]
    ))
    print("  ✅ score_match")

    # kick_off_parsed_resumes — reads tables + calls placement_runner
    pod.functions.replace_permissions("kick_off_parsed_resumes", FunctionPermissionsReplaceRequest(
        grants=[
            fn_grant("resumes",           "datastore_table", TABLE_READ),
            fn_grant("job_postings",      "datastore_table", TABLE_READ),
            fn_grant("job_matches",       "datastore_table", TABLE_READ),
            fn_grant("outreach_messages", "datastore_table", TABLE_READ),
            fn_grant("placement_runner",  "agent",           AGENT_PERMS),
        ]
    ))
    print("  ✅ kick_off_parsed_resumes")

    # send_telegram — reads user_profiles for bot token + chat_id
    pod.functions.replace_permissions("send_telegram", FunctionPermissionsReplaceRequest(
        grants=[
            fn_grant("user_profiles", "datastore_table", TABLE_READ),
        ]
    ))
    print("  ✅ send_telegram")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    pod_id = os.getenv("LEMMA_POD_ID")
    if not pod_id:
        print("❌ Missing LEMMA_POD_ID in environment.")
        sys.exit(1)

    print("🔐 Setting up Placement Pilot permissions...")
    print(f"   Pod ID: {pod_id[:8]}...")

    pod = Pod(pod_id=pod_id, timeout=120.0)

    try:
        setup_folders(pod)
        setup_agent_permissions(pod)
        setup_function_permissions(pod)
        print("\n✅ All permissions set!")
        print("\nFull setup order:")
        print("  1. python setup_pod.py")
        print("  2. python setup_permissions.py")
        print("  3. lemma workflow create --file ./placement_cycle.json")
        print("  4. streamlit run app.py")
    finally:
        pod.close()


if __name__ == "__main__":
    main()