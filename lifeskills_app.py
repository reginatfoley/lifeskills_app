from fasthtml.common import *
from monsterui.all import *
from datetime import datetime, timedelta

# Add this before your get() function
SECTION_IMAGES = {
    'CLEAN ROOM': '/static/images/room.jpg',
    'SELF CARE': '/static/images/brushing.jpg',
    'SCHOOL': '/static/images/classroom.jpg',
    'FAMILY': '/static/images/family.jpg'
}

app, rt = fast_app(hdrs=(
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src="https://cdn.jsdelivr.net/npm/uikit@3.16.19/dist/js/uikit.min.js"),
        Script(src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"),
        Theme.blue.headers()), live=True, static_path="static")
#live=True is used to enable live reload (no need toreload the page after changes)

# Store task states (in a real app, this would be in a database)
task_states = {}  # Format: {date_str: {task_id: bool}}

def get_date_key(offset=0):
    """Get standardized date key for storage"""
    date = datetime.now() + timedelta(days=offset)
    return date.strftime("%Y-%m-%d")


def make_task_card(task_name, task_id, offset=0):
    """Create a task card with state for specific date"""
    button_id = f"btn_{task_id}"
    date_key = get_date_key(offset)
    is_completed = task_states.get(date_key, {}).get(task_id, False)
    
    return Card(
        DivFullySpaced(
            P(task_name, cls=TextFont.bold_sm),
            Button(
                UkIcon("check"),
                cls=ButtonT.primary if not is_completed else "uk-button uk-button-success",
                hx_post=f"/day/{offset}/toggle/{task_id}" if offset else f"/toggle/{task_id}",
                hx_swap="outerHTML",
                id=button_id
            )
        ),
        cls="p-2"
    )


@rt("/toggle/{task_id}")
@rt("/day/{offset}/toggle/{task_id}")
def post(task_id: str, offset: int = 0):
    """Handle task toggling for any day (offset=0 is today)"""
    date_key = get_date_key(offset)
    
    # Initialize date in task_states if needed
    if date_key not in task_states:
        task_states[date_key] = {}
    
    # Toggle the task state for this date
    task_states[date_key][task_id] = not task_states[date_key].get(task_id, False)
    
    if all_tasks_completed(date_key):
        return Div(
            Button(
                UkIcon("check"),
                cls="uk-button uk-button-success",
                hx_post=f"/day/{offset}/toggle/{task_id}" if offset else f"/toggle/{task_id}",
                hx_swap="outerHTML",
                id=f"btn_{task_id}",
            ),
            Script("""
                // Your existing celebration code...
                UIkit.modal('#celebration-modal').show();
                
                setTimeout(() => {
                    const confettiConfig = {
                        particleCount: 150,
                        spread: 100,
                        origin: { y: 0.6 },
                        colors: ['#1e87f0', '#32d296', '#9c27b0'],
                        zIndex: 9999
                    };
                    
                    confetti(confettiConfig);
                    
                    setTimeout(() => {
                        confetti({
                            ...confettiConfig,
                            particleCount: 100,
                            angle: 60,
                            spread: 80,
                            origin: { x: 0 }
                        });
                        confetti({
                            ...confettiConfig,
                            particleCount: 100,
                            angle: 120,
                            spread: 80,
                            origin: { x: 1 }
                        });
                    }, 250);
                }, 100);
            """)
        )
    
    return Button(
        UkIcon("check"),
        cls=ButtonT.primary if not task_states[date_key].get(task_id, False) else "uk-button uk-button-success",
        hx_post=f"/day/{offset}/toggle/{task_id}" if offset else f"/toggle/{task_id}",
        hx_swap="outerHTML",
        id=f"btn_{task_id}"
    )


def parse_job_list(text_file = 'job_list.txt'):
    """
    Parse the job list text into a dictionary of categories and their tasks.
    Args: job_list_text (str): Raw text containing categories and tasks
    Returns: Dictionary with categories as keys and lists of tasks as values
    """
    categories = {}
    current_category = None
    
    # Open the file in read mode
    with open(text_file, 'r') as file:
        job_list_text = file.read()

    for line in job_list_text.split('\n'):
        line = line.strip()
        if line:
            if line.isupper():  # This is a category
                current_category = line
                categories[current_category] = []
            elif not line.startswith('_'):  # This is a task (ignore divider lines)
                categories[current_category].append(line)
    return categories


def create_section_with_image(category, tasks, image_url, start_task_id, offset=0):
    """Create a section with tasks on the left and an image on the right"""
    section_tasks = []
    for i, task in enumerate(tasks):
        task_id = start_task_id + i
        section_tasks.append(make_task_card(task, task_id, offset=offset))
    
    return Div(
        H2(category, cls=TextT.bold),
        DivFullySpaced(
            Div(*section_tasks, cls="w-2/3 space-y-2"),
            Img(src=image_url, alt=f"{category} image", cls="w-1/3 h-auto rounded-lg"),
        ),
        cls="space-y-4"
    )


def all_tasks_completed(date_key):
    """Check if all tasks are completed for a specific date"""
    # Get total number of tasks
    total_tasks = sum(len(tasks) for tasks in parse_job_list().values())
    
    # Get tasks for this date
    day_tasks = task_states.get(date_key, {})
    
    # Check if we have all tasks and they're all completed
    return len(day_tasks) == total_tasks and all(day_tasks.values())


def create_celebration_modal():
    return Div(
        Modal(
            ModalTitle("🎉 Congratulations! 🎉"),
            P("You've completed all your tasks for today!", cls=TextFont.bold_sm),
            P("Amazing job! Keep up the great work!", cls=TextFont.muted_sm),
            ModalCloseButton("Close", cls=ButtonT.primary),
            id="celebration-modal",
            cls="text-center"
        ),
        Audio(
            # Try with a direct URL to test
           src = "https://assets.mixkit.co/active_storage/sfx/974/974-preview.mp3",
            # src = "/static/sounds/success.mp3",
            id="celebration-sound",
            controls=True,
            preload="auto"
        )
    )


@rt("/")
@rt("/day/{offset}")
def get(offset: int = 0):
    """Handle both main route and day-specific routes"""
    # Calculate the date based on offset
    target_date = datetime.now() + timedelta(days=offset)
    date_str = target_date.strftime("%A, %B %d, %Y")
    
    # Create tab navigation with dynamic active states
    tabs = TabContainer(
        Li(A("Today", href="/", cls="uk-active" if offset == 0 else "")),
        Li(A("Yesterday", href="/day/-1", cls="uk-active" if offset == -1 else "")),
        Li(A("Tomorrow", href="/day/1", cls="uk-active" if offset == 1 else "")),
        Li(A("This Week", href="/week")),
        alt=True
    )
    
    header = Div(
        tabs,
        P(date_str, cls=TextFont.muted_lg),
        H1("Daily Tasks", cls=TextT.bold),
        P("Track your progress through the week", cls=TextFont.muted_sm),
        DividerLine(),
        cls="space-y-2"
    )

    # Create sections
    categories = parse_job_list()
    sections = []
    task_id = 0
    for category, tasks in categories.items():
        section = create_section_with_image(
            category,
            tasks,
            SECTION_IMAGES[category],
            task_id,
            offset=offset
        )
        sections.append(section)
        task_id += len(tasks)

    return Container(header, *sections, create_celebration_modal(), cls="space-y-8")


@rt
def index(): 
    card = get()
    return Titled(card)

serve()


