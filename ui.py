import streamlit as st
import app as core


# ==========================================
# 1. Page Configuration
# ==========================================

st.set_page_config(
    page_title="CreativeOps",
    page_icon="🎬",
    layout="wide"
)


# ==========================================
# 2. Page Header
# ==========================================

st.title("🎬 CreativeOps")
st.subheader("AI-Powered Campaign Production System")

st.write(
    "Transform your campaign idea into a structured "
    "video production plan."
)

st.divider()


# ==========================================
# 3. Campaign Brief
# ==========================================

st.header("Campaign Brief")

campaign_idea = st.text_area(
    "Campaign Idea",
    placeholder="Describe your campaign idea...",
    height=120
)

campaign_type = st.selectbox(
    "Campaign Type",
    [
        "Product",
        "Business / Place",
        "Event",
        "Sports",
        "Brand Awareness",
        "Service",
        "Other"
    ]
)

col1, col2 = st.columns(2)

with col1:

    brand = st.text_input(
        "Brand / Organization"
    )

    campaign_goal = st.text_input(
        "Campaign Goal",
        placeholder="e.g. Brand awareness, promotion..."
    )

    target_audience = st.text_input(
        "Target Audience",
        placeholder="e.g. Young adults, professionals..."
    )

with col2:

    key_message = st.text_input(
        "Key Message"
    )

    tone_and_style = st.text_input(
        "Tone and Style",
        placeholder="e.g. Cinematic, emotional, energetic..."
    )


# ==========================================
# 4. Additional Information
# ==========================================

st.divider()

st.subheader("Additional Information")

st.caption(
    "Add any extra verified campaign details. "
    "This section is optional."
)


if "additional_details" not in st.session_state:
    st.session_state.additional_details = []


for detail_id in st.session_state.additional_details:

    col1, col2, col3 = st.columns([2, 3, 0.5])

    with col1:

        st.text_input(
            "Detail Name",
            key=f"detail_name_{detail_id}",
            placeholder="e.g. Location"
        )

    with col2:

        st.text_input(
            "Detail Value",
            key=f"detail_value_{detail_id}",
            placeholder="e.g. Riyadh"
        )

    with col3:

        st.write("")

        if st.button(
            "✕",
            key=f"delete_{detail_id}"
        ):

            st.session_state.additional_details.remove(detail_id)
            st.rerun()


if st.button("➕ Add another detail"):

    new_id = (
        max(st.session_state.additional_details, default=0) + 1
    )

    st.session_state.additional_details.append(new_id)
    st.rerun()


# ==========================================
# 5. Production Output Parser
# ==========================================

def parse_production_output(raw_output):

    shots = []

    for line in raw_output.splitlines():

        line = line.strip()

        if not line.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip("|").split("|")
        ]

        if len(cells) != 7:
            continue

        # Skip Markdown table header
        if cells[0].lower() == "shot":
            continue

        # Skip Markdown separator rows
        if all(
            cell and set(cell) <= {"-", ":"}
            for cell in cells
        ):
            continue

        shot_number = core.normalize_shot_number(cells[0])

        if shot_number is None:
            continue

        shots.append({
            "shot": cells[0],
            "shot_number": shot_number,
            "duration": cells[1],
            "camera": cells[2],
            "movement": cells[3],
            "subject_action": cells[4],
            "lighting": cells[5],
            "audio": cells[6]
        })

    if not shots:

        raise ValueError(
            "Could not read the Production Agent shot list."
        )

    return shots


# ==========================================
# 6. Display Production Plan
# ==========================================

def display_production_plan(
    creative_output,
    production_shots,
    data
):

    tasks = data["tasks"]

    task_lookup = {}

    for task in tasks:

        shot_number = core.normalize_shot_number(task["shot"])

        if shot_number is not None:
            task_lookup[shot_number] = task

    total_duration = sum(
        task["duration_seconds"]
        for task in tasks
        if task["duration_seconds"] > 0
    )

    # ------------------------------------------
    # Custom Styling
    # ------------------------------------------

    st.markdown("""
        <style>
        .plan-header {
            padding: 10px 0 18px 0;
        }

        .section-label {
            color: #A0A0A0;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        div[data-testid="stMetric"] {
            background: rgba(128,128,128,0.08);
            padding: 16px;
            border-radius: 10px;
            border: 1px solid rgba(128,128,128,0.18);
        }
        </style>
    """, unsafe_allow_html=True)

    # ------------------------------------------
    # Production Plan Header
    # ------------------------------------------

    st.divider()

    st.markdown(
        '<div class="plan-header">'
        '<div class="section-label">CAMPAIGN OUTPUT</div>'
        '<h1 style="margin:0;">Production Plan</h1>'
        '<p style="color:#A0A0A0;">'
        'Your campaign has been transformed into a production-ready plan.'
        '</p></div>',
        unsafe_allow_html=True
    )

    # ------------------------------------------
    # Summary
    # ------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            label="Total Shots",
            value=len(production_shots)
        )

    with col2:

        st.metric(
            label="Total Duration",
            value=f"{total_duration:g} sec"
        )

    with col3:

        st.metric(
            label="Production Tasks",
            value=len(tasks)
        )

    # ------------------------------------------
    # Creative Script
    # ------------------------------------------

    st.markdown("### Creative Script")

    with st.expander(
        "View Campaign Script",
        expanded=False
    ):

        st.markdown(creative_output)

    # ------------------------------------------
    # Shot Breakdown
    # ------------------------------------------

    st.markdown("### Shot Breakdown")

    st.caption(
        "Explore each shot to view its filming details "
        "and production responsibilities."
    )

    displayed_task_ids = set()

    for index, shot in enumerate(production_shots):

        task = task_lookup.get(shot["shot_number"])

        duration = shot["duration"]

        with st.expander(
            f"SHOT {shot['shot_number']}  •  {duration} SECONDS",
            expanded=(index == 0)
        ):

            # Camera Setup & Visual Direction

            st.markdown(
                '<div class="section-label">'
                'CAMERA & VISUAL DIRECTION'
                '</div>',
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)

            with col1:

                st.markdown("**Camera**")
                st.write(shot["camera"])

                st.markdown("**Movement**")
                st.write(shot["movement"])

                st.markdown("**Lighting**")
                st.write(shot["lighting"])

            with col2:

                st.markdown("**Subject Action**")
                st.write(shot["subject_action"])

                st.markdown("**Audio**")
                st.write(shot["audio"])

            # Production Instructions & Crew

            if task:

                displayed_task_ids.add(task["id"])

                st.divider()

                st.markdown(
                    '<div class="section-label">'
                    'PRODUCTION INSTRUCTIONS'
                    '</div>',
                    unsafe_allow_html=True
                )

                st.write(task["description"])

                st.divider()

                st.markdown(
                    '<div class="section-label">'
                    'CREW RESPONSIBILITIES'
                    '</div>',
                    unsafe_allow_html=True
                )

                roles = task.get("roles", {})

                for role, responsibility in roles.items():

                    st.markdown(f"**{role}**")
                    st.write(responsibility)

    # ------------------------------------------
    # Additional Production Tasks
    # ------------------------------------------

    additional_tasks = [
        task for task in tasks
        if task["id"] not in displayed_task_ids
    ]

    if additional_tasks:

        st.divider()

        st.markdown("### Additional Production Tasks")

        for task in additional_tasks:

            with st.expander(
                f"Task {task['id']}  •  {task['shot']}",
                expanded=False
            ):

                st.markdown("**Duration**")

                st.write(
                    f"{task['duration_seconds']} seconds"
                )

                st.markdown("**Production Instructions**")

                st.write(task["description"])

                st.markdown("**Crew Responsibilities**")

                roles = task.get("roles", {})

                if isinstance(roles, dict) and roles:
                    for role, responsibility in roles.items():
                        with st.container(border=True):
                            st.markdown(f"**{role}**")
                            st.write(responsibility)
                else:
                    st.caption("No crew responsibilities available.")


# ==========================================
# 7. Generate Production Plan
# ==========================================

st.divider()

if st.button(
    "Generate Production Plan",
    type="primary",
    use_container_width=True
):

    if not campaign_idea.strip():

        st.error("Please enter a campaign idea.")

    else:

        verified_information = {}

        for detail_id in st.session_state.additional_details:

            name = st.session_state.get(
                f"detail_name_{detail_id}", ""
            ).strip()

            value = st.session_state.get(
                f"detail_value_{detail_id}", ""
            ).strip()

            if name and value:
                verified_information[name] = value

        campaign_brief = {
            "campaign_type": campaign_type,
            "brand_or_organization": brand.strip() or "Not provided",
            "campaign_goal": campaign_goal.strip() or "Not provided",
            "target_audience": target_audience.strip() or "Not provided",
            "key_message": key_message.strip() or "Not provided",
            "tone_and_style": tone_and_style.strip() or "Not provided",
            "verified_information": verified_information
        }

        try:

            with st.spinner(
                "AI agents are working on your campaign..."
            ):

                result = core.run_project(
                    campaign_idea.strip(),
                    campaign_brief,
                    max_attempts=1
                )

                # Validate and save Operations JSON
                operations_data = core.validate_result(result)

                # Extract agent outputs
                creative_output = result.tasks_output[0].raw

                production_output = result.tasks_output[1].raw

                production_shots = parse_production_output(
                    production_output
                )

            # Store results in session
            st.session_state.generated_plan = {
                "creative_output": creative_output,
                "production_shots": production_shots,
                "operations_data": operations_data
            }

            st.session_state.generation_error = None

        except Exception:

            st.session_state.generated_plan = None

            st.session_state.generation_error = (
                "We couldn't generate your production plan. "
                "Please try again."
            )


# ==========================================
# 8. Display Results
# ==========================================

if st.session_state.get("generation_error"):

    st.error(
        st.session_state.generation_error
    )

elif st.session_state.get("generated_plan"):

    plan = st.session_state.generated_plan

    display_production_plan(
        plan["creative_output"],
        plan["production_shots"],
        plan["operations_data"]
    )
