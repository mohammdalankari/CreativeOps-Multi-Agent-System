import os
import time
import json
import re
import math
import argparse
import sys
import logging
import io
from contextlib import redirect_stdout, redirect_stderr
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


# 1. API Configuration
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

groq_llm = LLM(
    model="openai/openai/gpt-oss-120b",
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
    custom_openai=True,
    temperature=0.3,
    max_tokens=8000
)


# 2. Agents
creative_agent = Agent(
    role="Senior Creative Copywriter",
    goal="Write an engaging 30-second commercial script.",
    backstory="An award-winning advertising copywriter.",
    verbose=False,
    allow_delegation=False,
    llm=groq_llm
)

production_agent = Agent(
    role="Video Production Director",
    goal="Convert the script into a detailed shot list.",
    backstory="An experienced video production director.",
    verbose=False,
    allow_delegation=False,
    llm=groq_llm
)

operations_agent = Agent(
    role="Creative Operations Manager",
    goal="Convert production requirements into JSON tasks.",
    backstory="An organized creative operations manager.",
    verbose=False,
    allow_delegation=False,
    llm=groq_llm
)


# 3. Tasks


creative_task = Task(
    description="""
    Write a professional 30-second commercial script
    based on this idea: {idea}

    CAMPAIGN BRIEF:
    {campaign_brief}

    REQUIREMENTS:

    1. Identify the campaign type and adapt the creative approach accordingly.
    2. Establish the relevant brand, organization, event, place,
       service or subject clearly.
    3. Define the target audience and core advertising message
       using the supplied campaign brief.
    4. Create a clear beginning, middle and ending.
    5. Include chronological scenes with timestamps.
    6. Include voice-over, dialogue and visual descriptions.
    7. Keep the script realistic and suitable for a 30-second ad.
    8. Include a clear brand or campaign reveal and call to action
       when appropriate.
    9. Every scene must contribute to the campaign's main message.
    10. Do not add unrelated scenes or visual elements.
    11. Ensure all scene durations total exactly 30 seconds.
    12. Use supplied information as the source of truth for factual claims.

    CAMPAIGN ACCURACY:

    - Treat empty fields and "Not provided" as unknown information.
    - Never invent dates, locations, prices, statistics, participants,
      product specifications, services or official partnerships.
    - Do not turn missing information into assumed facts.
    - Do not present fictional capabilities or events as real.
    - Do not invent websites, social media accounts or contact details.
    - Creative storytelling, metaphors and fictional visual concepts
      are allowed, provided they are not presented as factual claims.
    - Do not confuse the campaign's desired message with verified facts.
    - If a factual detail is missing, avoid mentioning it rather
      than making an assumption.
    - Never expand a verified technical specification into
    additional performance claims.
    - Bluetooth 5.3 does not automatically mean instant,
    lag-free, or uninterrupted connectivity.
    - Do not imply noise cancellation or sound isolation
    unless explicitly confirmed.
    - When presenting battery life, always preserve
    qualifiers such as "up to".
    - Do not invent physical product features, indicators,
    logos, or accessories as confirmed product details.
    Treat them only as proposed visual concepts.
      
    CREATIVE CONCEPT VS VERIFIED FACTS:

    - Clearly distinguish proposed visual concepts from confirmed
    campaign information.
    - Do not imply that proposed venues, equipment, demonstrations,
    logos, facilities or technologies actually exist.
    - When using speculative visual concepts, identify them as
    proposed creative visuals rather than factual campaign details.
    - Do not claim that an official logo, website, social account
    or registration channel exists unless provided.
    - If no verified CTA channel is available, use a general
    campaign-focused CTA that does not require an external link
    or account.
    - Avoid unnecessary fictional details that do not improve
    the commercial.

    CAMPAIGN TYPE GUIDANCE:

    - Product: Focus on supplied features and verified specifications.
    - Business or Place: Focus on supplied services, atmosphere,
      location and verified business information.
    - Event: Focus on supplied event details, dates and venue.
    - Sports: Use only supplied or verified competition information.
    - Brand Awareness: Focus on supplied identity, values and message.
    - Service: Focus on supplied service benefits and capabilities.
    - Other: Adapt creatively while preserving factual accuracy.

    Output a structured commercial script.
    """,
    expected_output=(
        "A structured 30-second commercial script containing "
        "campaign identity, target audience, core message, "
        "timestamped scenes, visual directions, voice-over, "
        "dialogue and call to action."
    ),
    agent=creative_agent
)


production_task = Task(
    description="""
    Analyze the creative script and create a professional,
    realistic, chronological shot list for a 30-second commercial.

    STRICT REQUIREMENTS:

    1. The commercial must have a total duration of exactly 30 seconds.

    2. Every shot must include:
       - Shot number
       - Duration in seconds
       - Camera framing and lens
       - Camera movement
       - Subject action
       - Lighting setup
       - Audio or voice-over when relevant

    3. Camera and equipment realism:
       - Never describe a dolly movement as a zoom or lens change.
       - Do not change lenses during a continuous shot.
       - Do not combine incompatible camera movements.
       - Keep each shot achievable with realistic equipment.

       PRODUCTION BUDGET AND PRACTICALITY:

        - Assume a practical, cost-conscious production unless
        a specific budget or production scale is provided.
        - Prefer one primary camera setup throughout the commercial
        unless a different camera is genuinely necessary.
        - Avoid unnecessary camera brand and model specifications.
        - Use equipment that is commonly available to a small
        professional production crew.
        - Avoid expensive CGI, complex sets and specialized technology
        unless essential to the creative concept.
        - Clearly identify proposed VFX or CGI requirements.
        - Prefer simple practical alternatives when they achieve
        a similar visual result.
        - For low-budget campaigns, prioritize one filming
        location whenever possible.
        - Prefer natural lighting and simple camera setups.
        - Avoid unnecessary Steadicam, crane, dolly, and
        complex lighting setups.
        - Use static or handheld shots when they achieve
        the same storytelling purpose.
        - Minimize location changes, equipment, crew, and
        setup time.
        - Production recommendations must reflect the
        specified budget, not just the desired visual style.

    4. Production roles:
       - Assign responsibilities only to relevant crew members.
       - Do not assign artificial lighting tasks to drone operators.
       - Do not require unnecessary equipment or crew.

    4.5. Production consistency checks:
       - Camera movement must match the equipment and camera setup.
       - Never assign camera filters to the Gaffer.
       - Never request sound effects that cannot physically exist.
       - Do not create movement durations longer than the shot itself.
       - Do not use impractical lighting setups for moving outdoor subjects.
       - Voice-over recording must be treated as post-production,
         unless explicitly requested as live dialogue.
       - Clearly separate CGI, animation and post-production
         from live-action camera shots.
       - Every role and piece of equipment must have a
         clear and necessary purpose.

    5. Timing:
       - All commercial shots must add up to exactly 30 seconds.
       - Do not create optional commercial shots.
       - Do not include post-production tasks in the timed shot list.
       - Make shot durations realistic for the actions shown.

    6. Post-production:
       - Mention VFX or editing requirements as notes only.
       - Do not present post-production as live camera operations.

    7. Continuity:
       - Preserve the script's story, product details and voice-over.
       - Keep the shots in chronological order.
       - Avoid duplicate shots and contradictory instructions.

    8. Output a clearly structured shot list.
       Do not output JSON. The Operations Agent handles JSON conversion.
       Output exactly one pipe-separated Markdown table.
       Use this exact header:
       | Shot | Duration (seconds) | Camera | Movement | Subject Action | Lighting | Audio |
       Put one shot per row and do not use prose, bullet lists or
       additional tables outside this single shot table.

    9. Script fidelity:
       - Preserve every important scene, product feature,
         brand message and key visual from the original script.
       - Do not invent unrelated scenes or activities.
       - Do not remove the final brand reveal or call to action.
       - Every shot must serve the original commercial concept.
       - If the script cannot fit into 30 seconds,
         prioritize the core message without changing its meaning.

    10. Campaign Accuracy:
       - Preserve all verified campaign information.
       - Do not invent product features, business services,
         event details, dates, locations, statistics or claims.
       - Do not introduce factual claims that were not in the script
         or supplied campaign brief.
       - Visual representations must not contradict the campaign brief.
       - Creative visual storytelling is allowed, but must not
         imply unsupported facts.
       - Treat missing campaign information as unknown.
       - Clearly distinguish proposed production concepts
         from confirmed campaign facilities and equipment.
       - Do not assume that visual concepts proposed by the
         Creative Agent are available at the actual location.


    """,
    expected_output=(
        "A chronological, production-ready shot list for a "
        "30-second commercial, with realistic camera setups, "
        "lighting, actions, audio and timing."
    ),
    agent=production_agent,
    context=[creative_task]
)


operations_task = Task(
    description="""
    Convert the production shot list into structured production tasks.

    CRITICAL RULE: You are converting the shot list, NOT redesigning it.
    Preserve the production plan exactly.

    Requirements:

    1. Return ONLY valid JSON. No Markdown or code fences.

    2. Use this exact structure:
       {
         "tasks": [
           {
             "id": 1,
             "shot": "Shot 1",
             "duration_seconds": 3,
             "description": "Detailed production instructions",
             "roles": {
               "Director": "Responsibilities",
               "CameraOperator": "Responsibilities"
             }
           }
         ]
       }

    3. SHOT PRESERVATION:
       - Create exactly one task for every shot in the production shot list.
       - Do not skip, remove, merge, split, or duplicate any shot.
       - Preserve the original shot numbers and chronological order.
       - Every production shot must appear in the final JSON.
       - Do not invent additional commercial shots.

    4. DURATION PRESERVATION:
       - Copy each shot's duration_seconds EXACTLY as specified
         in the production shot list.
       - NEVER redistribute, increase, decrease, or optimize
         individual shot durations.
       - Do not change durations to force the total to 30 seconds.
       - The production shot list is the source of truth.
       - If the source durations do not total exactly 30 seconds,
         preserve them without changing them.

    5. COMMERCIAL DURATION:
       - The commercial shots should total exactly 30 seconds.
       - Calculate the total duration internally before returning.
       - Do not sacrifice shot preservation to satisfy this rule.

    6. POST-PRODUCTION:
       - Keep post-production tasks separate from commercial shots.
       - Do not assign commercial shot durations to post-production.
       - Do not let post-production tasks affect the 30-second total.

    7. DESCRIPTIONS:
       - Preserve the original visual action and production intent.
       - You may clarify instructions, but must not change the
         creative concept or introduce unrelated actions.
       - Keep equipment instructions consistent with the
         production shot list.

    8. TASK IDs:
       - Every task must have a unique integer ID.
       - IDs must follow chronological order.

    9. ROLES:
       - Assign only roles relevant to each task.
       - Do not assign responsibilities that conflict with
         the production instructions.

    10. FINAL CHECK:
        - Verify that every source shot appears exactly once.
        - Verify that shot order is unchanged.
        - Verify that every duration matches its source shot.
        - Verify that no commercial shot was removed.
        - Return valid JSON only.

    11. CAMPAIGN ACCURACY:
       - Preserve campaign details from the production shot list.
       - Do not introduce new factual claims or specifications.
       - Do not add unsupported product capabilities,
         business services or event information.
       - Preserve the original campaign concept and message.


    """,
    expected_output=(
        "A valid JSON object containing every production shot "
        "exactly once, in the original order, with unchanged "
        "durations and unique task IDs."
    ),
    agent=operations_agent,
    context=[production_task]
)


# 4. Crew
creative_ops_crew = Crew(
    agents=[
        creative_agent,
        production_agent,
        operations_agent
    ],
    tasks=[
        creative_task,
        production_task,
        operations_task
    ],
    process=Process.sequential,
    verbose=False
)


# 5. User Input

def get_user_input():

    print("\n================================")
    print("   CreativeOps Multi-Agent System")
    print("================================")

    print("\n--- Campaign Idea ---")

    while True:
        campaign_idea = input(
            "\nDescribe the campaign idea: "
        ).strip()

        if campaign_idea:
            break

        print("Campaign idea cannot be empty.")

    print("\n--- Campaign Information ---")

    campaign_types = [
        "Product",
        "Business / Place",
        "Event",
        "Sports",
        "Brand Awareness",
        "Service",
        "Other"
    ]

    print("\nCampaign types:")
    for index, campaign_type in enumerate(campaign_types, start=1):
        print(f"{index}. {campaign_type}")

    while True:
        choice = input("\nSelect campaign type (1-7): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(campaign_types):
            campaign_type = campaign_types[int(choice) - 1]
            break

        print("Please select a valid number.")

    def get_field(prompt):
        return input(prompt).strip() or "Not provided"

    brand_or_organization = get_field(
        "Brand / Organization name: "
    )

    campaign_goal = get_field(
        "Campaign goal (awareness, promotion, engagement...): "
    )

    target_audience = get_field(
        "Target audience: "
    )

    key_message = get_field(
        "Main campaign message: "
    )

    tone_and_style = get_field(
        "Tone and style (cinematic, funny, emotional...): "
    )

    print(
        "\nAdditional campaign information "
        "(enter one detail per line as: name: value)."
    )
    print("Examples: Location: Riyadh | Date: December 2026")
    print("Press Enter on an empty line when finished.")

    verified_information = {}

    while True:
        detail_input = input("> ").strip()

        if not detail_input:
            break

        if ":" not in detail_input:
            print("Use this format: name: value")
            continue

        detail_name, detail_value = detail_input.split(":", 1)

        detail_name = detail_name.strip()
        detail_value = detail_value.strip()

        if not detail_name or not detail_value:
            print("Both detail name and value are required.")
            continue

        verified_information[detail_name] = detail_value

    campaign_brief = {
        "campaign_type": campaign_type,
        "brand_or_organization": brand_or_organization,
        "campaign_goal": campaign_goal,
        "target_audience": target_audience,
        "key_message": key_message,
        "tone_and_style": tone_and_style,
        "verified_information": verified_information
    }

    return campaign_idea, campaign_brief


def print_input_summary(campaign_idea, campaign_brief):
    print("\n================================")
    print("       INPUT SUMMARY")
    print("================================")
    print("\nCampaign idea:")
    print(campaign_idea)
    print("\nCampaign brief:")
    print(
        json.dumps(
            campaign_brief,
            ensure_ascii=False,
            indent=2
        )
    )


# 6. Execution with retry

def run_project(idea, campaign_brief, max_attempts=3):

    for attempt in range(1, max_attempts + 1):

        try:
            llm_logger = logging.getLogger("crewai.llms.base_llm")
            previous_log_level = llm_logger.level
            llm_logger.setLevel(logging.ERROR)
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    result = creative_ops_crew.kickoff(
                        inputs={
                            "idea": idea,
                            "campaign_brief": json.dumps(
                                campaign_brief,
                                ensure_ascii=False,
                                indent=2
                            )
                        }
                    )
            finally:
                llm_logger.setLevel(previous_log_level)

            return result

        except Exception as error:

            print(f"\n❌ Attempt {attempt} failed: {error}")

            if attempt == max_attempts:
                raise

            wait_time = 5 * (2 ** (attempt - 1))

            print(f"⏳ Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


# 7. Validation Helpers

def clean_json_output(raw_output):
    output = raw_output.strip()

    output = re.sub(
        r"^```(?:json)?\s*",
        "",
        output,
        flags=re.IGNORECASE
    )

    output = re.sub(r"\s*```$", "", output)

    return output.strip()


def normalize_shot_number(value):

    value = re.sub(r"[*`]", "", str(value)).strip()

    match = re.fullmatch(
        r"(?:Shot\s*)?(\d+[a-z]?)",
        value,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(1).lower()


def parse_production_shots(production_output):

    source_shots = []

    for line in production_output.splitlines():

        if "|" not in line:
            continue

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        if len(cells) < 2:
            continue

        shot_number = normalize_shot_number(cells[0])

        if shot_number is None:
            continue

        duration_text = re.sub(r"[*`]", "", cells[1])

        duration_match = re.search(
            r"\d+(?:\.\d+)?",
            duration_text
        )

        if not duration_match:
            continue

        duration = float(duration_match.group())

        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(
                f"Invalid duration in Production Shot {shot_number}"
            )

        source_shots.append((shot_number, duration))

    if not source_shots:
        raise ValueError(
            "Could not extract shots from Production output. "
            "Check the Production shot list table format."
        )

    return source_shots


# 8. Main Execution and Validation

def print_crew_completion(result):
    if not hasattr(result, "tasks_output") or len(result.tasks_output) < 3:
        return

    completion = (
        "Crew Execution Completed\n"
        "Name: crew\n"
        "Final Output:\n"
        f"{result.tasks_output[2].raw}"
    )

    Console().print(
        Panel(
            Text(completion),
            title="Crew Completion",
            expand=True
        )
    )


def save_output_json(data):
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "output.json"
    )
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")


def validate_result(result):
    if len(result.tasks_output) < 3:
        raise ValueError("Expected outputs from all three agents.")

    production_output = result.tasks_output[1].raw
    operations_output = result.raw
    source_shots = parse_production_shots(production_output)

    output = clean_json_output(operations_output)
    data = json.loads(output)

    if not isinstance(data, dict):
        raise ValueError("JSON output must be an object.")

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("Tasks must be a non-empty list.")

    required_fields = [
        "id",
        "shot",
        "duration_seconds",
        "description",
        "roles"
    ]

    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Every task must be a JSON object.")

        for field in required_fields:
            if field not in task or task[field] is None:
                raise ValueError(
                    f"Task {task.get('id', 'Unknown')} is missing: {field}"
                )

        if not isinstance(task["id"], int) or isinstance(task["id"], bool):
            raise ValueError(f"Task ID must be an integer: {task['id']}")
        if not isinstance(task["shot"], str):
            raise ValueError(f"Invalid shot name in Task {task['id']}")
        if not isinstance(task["description"], str):
            raise ValueError(f"Invalid description in Task {task['id']}")
        if not task["description"].strip():
            raise ValueError(
                f"Empty description in Task {task['id']}"
            )
        if not isinstance(task["roles"], dict):
            raise ValueError(f"Roles must be an object in Task {task['id']}")
        if not task["roles"]:
            raise ValueError(
                f"Empty roles in Task {task['id']}"
            )

        duration = task["duration_seconds"]
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration < 0
        ):
            raise ValueError(f"Invalid duration in Task {task['id']}")

    task_ids = [task["id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Duplicate task IDs detected!")
    if task_ids != sorted(task_ids):
        raise ValueError("Task IDs are not in chronological order!")

    commercial_tasks = [
        task for task in tasks
        if task["duration_seconds"] > 0
    ]
    operations_shots = []

    for task in commercial_tasks:
        shot_number = normalize_shot_number(task["shot"])
        if shot_number is None:
            raise ValueError(f"Invalid shot reference: {task['shot']}")
        operations_shots.append(
            (shot_number, float(task["duration_seconds"]))
        )

    operation_numbers = [number for number, _ in operations_shots]
    if len(operation_numbers) != len(set(operation_numbers)):
        raise ValueError("Duplicate operations shot references detected!")

    if len(source_shots) != len(operations_shots):
        raise ValueError(
            f"Shot count mismatch: Production has {len(source_shots)}, "
            f"Operations has {len(operations_shots)}"
        )

    for index, (source, operation) in enumerate(
        zip(source_shots, operations_shots),
        start=1
    ):
        source_number, source_duration = source
        operation_number, operation_duration = operation

        if source_number != operation_number:
            raise ValueError(
                f"Shot order mismatch at position {index}: "
                f"Production has {source_number}, "
                f"Operations has {operation_number}"
            )
        if abs(source_duration - operation_duration) > 0.001:
            raise ValueError(
                f"Duration mismatch in Shot {source_number}: "
                f"Production has {source_duration}s, "
                f"Operations has {operation_duration}s"
            )

    source_total = sum(duration for _, duration in source_shots)
    if abs(source_total - 30) > 0.01:
        raise ValueError(
            f"Production duration must be 30 seconds, got {source_total}"
        )

    total_duration = sum(
        task["duration_seconds"]
        for task in commercial_tasks
    )
    if abs(total_duration - 30) > 0.01:
        raise ValueError(
            f"Operations duration must be 30 seconds, got {total_duration}"
        )

    save_output_json(data)

    print("\n================================")
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("================================")
    print("Total tasks:", len(tasks))
    print("Production shots:", len(source_shots))
    print("Operations shots:", len(commercial_tasks))
    print("Total duration:", total_duration)
    print("✅ JSON is valid")
    print("✅ Task IDs are unique")
    print("✅ All required fields exist")
    print("✅ Shot count matches")
    print("✅ Shot order matches")
    print("✅ Individual durations match")
    print("✅ Commercial duration is exactly 30 seconds")
    print("✅ JSON saved to output.json")
    return data


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a validated 30-second campaign production plan."
    )

    parser.add_argument("--idea", help="Campaign idea")

    parser.add_argument(
        "--brief-json",
        help="Campaign brief as a JSON object"
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum complete kickoff and validation attempts"
    )

    return parser.parse_args()



if __name__ == "__main__":
    args = parse_args()

    if args.max_attempts < 1:
        print("❌ --max-attempts must be at least 1.")
        sys.exit(2)

    if args.idea or args.brief_json:

        if not args.idea or not args.brief_json:
            print(
                "❌ --idea and --brief-json must be provided together."
            )
            sys.exit(2)

        campaign_idea = args.idea.strip()

        if not campaign_idea:
            print("❌ Campaign idea cannot be empty.")
            sys.exit(2)

        try:
            campaign_brief = json.loads(args.brief_json)

        except json.JSONDecodeError as error:
            print(f"❌ Invalid --brief-json: {error}")
            sys.exit(2)

        if not isinstance(campaign_brief, dict):
            print("❌ --brief-json must describe a JSON object.")
            sys.exit(2)

    else:
        campaign_idea, campaign_brief = get_user_input()

    print_input_summary(campaign_idea, campaign_brief)

    for attempt in range(1, args.max_attempts + 1):

        try:
            result = run_project(
                campaign_idea,
                campaign_brief,
                max_attempts=1
            )

            print_crew_completion(result)
            validate_result(result)
            sys.exit(0)

        except json.JSONDecodeError as error:
            print(f"\n❌ Invalid JSON: {error}")

        except (ValueError, KeyError, TypeError, IndexError) as error:
            print(f"\n❌ Validation failed: {error}")

        except Exception as error:
            print(f"\n❌ Attempt {attempt} failed: {error}")

        if attempt < args.max_attempts:
            wait_time = 5 * (2 ** (attempt - 1))
            print(f"⏳ Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    print("\n❌ All attempts failed.")
    sys.exit(1)