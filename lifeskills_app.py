from fasthtml.common import *
from monsterui.all import *
from datetime import datetime


app, rt = fast_app(
    hdrs=(
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src="https://cdn.jsdelivr.net/npm/uikit@3.16.19/dist/js/uikit.min.js"),
        Script(src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"),
        Theme.blue.headers()
    ),
    static_path="static"  # Add this line
)
#live=True is used to enable live reload (no need toreload the page after changes)

# Store task states (in a real app, this would be in a database)
task_states = {}

def make_task_card(task_name, task_id):
    button_id = f"btn_{task_id}"
    return Card(
        DivFullySpaced(
            P(task_name, cls=TextFont.bold_sm),
            Button(
                UkIcon("check"),
                cls=ButtonT.primary if not task_states.get(task_id, False) else "uk-button uk-button-success",
                hx_post=f"/toggle/{task_id}",
                hx_swap="outerHTML",
                id=button_id
            )
        ),
        cls="p-1"
    )


@rt("/toggle/{task_id}")
def post(task_id: str):
    task_states[task_id] = not task_states.get(task_id, False)
    
    if all_tasks_completed():
        return Div(
            Button(
                UkIcon("check"),
                cls="uk-button uk-button-success",
                hx_post=f"/toggle/{task_id}",
                hx_swap="outerHTML",
                id=f"btn_{task_id}",
            ),
            Script("""
                // First play the sound
                const playSound = async () => {
                    try {
                        const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/974/974-preview.mp3');
                        audio.volume = 0.5;
                        await audio.play();
                    } catch (error) {
                        console.log('Audio play failed:', error);
                    }
                };

                // Execute everything in sequence
                (async () => {
                    await playSound();
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
                })();
            """)
        )
    
    return Button(
        UkIcon("check"),
        cls=ButtonT.primary if not task_states[task_id] else "uk-button uk-button-success",
        hx_post=f"/toggle/{task_id}",
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

def create_section_with_image(category, tasks, image_url, start_task_id):
    """
    Create a section with tasks on the left and an image on the right
    
    Args:
        category (str): Category name
        tasks (list): List of tasks
        image_url (str): URL/path to the image
        start_task_id (int): Starting ID for tasks in this section
    """
    # Create task cards with smaller size
    section_tasks = []
    for i, task in enumerate(tasks):
        task_id = start_task_id + i
        section_tasks.append(make_task_card(task, task_id))
    
    return Div(
        H2(category, cls=TextT.bold),
        DivFullySpaced(
            # Tasks on the left (using 2/3 of space)
            # Grid(*section_tasks, cols=1, gap=2, cls="w-2/3"),
            Div(*section_tasks, cls="w-2/3 space-y-2"),  # Added space between cards
            # Image on the right (using 1/3 of space)
            Img(src=image_url, alt=f"{category} image", cls="w-1/3 h-auto rounded-lg"),
        ),
        cls="space-y-4"
    )

# Add this before your get() function
SECTION_IMAGES = {
    'CLEAN ROOM': '/static/images/room.jpg',
    'SELF CARE': '/static/images/brushing.jpg',
    'SCHOOL': '/static/images/classroom.jpg',
    'FAMILY': '/static/images/family.jpg'
}


def all_tasks_completed():
    """Check if all tasks are marked as completed"""
     # Get total number of tasks from all categories
    total_tasks = sum(len(tasks) for tasks in parse_job_list().values())
    
    # Check if we have the right number of completed tasks
    if len(task_states) != total_tasks:
        return False
        
    # Check if all existing tasks are completed
    return all(task_states.values())




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
def get():
    today = datetime.now()
    date_str = today.strftime("%A, %B %d, %Y")
    
    header = Div(
        P(date_str, cls=TextFont.muted_lg),
        H1("Daily Tasks", cls=TextT.bold),
        P("Track your progress through the week", cls=TextFont.muted_sm),
        DividerLine(),
        cls="space-y-2"
    )

    # Get tasks using the parsing function
    categories = parse_job_list()
    
    # Create sections with images
    sections = []
    task_id = 0
    for category, tasks in categories.items():
        section = create_section_with_image(category, tasks, SECTION_IMAGES[category], task_id)
        sections.append(section)
        task_id += len(tasks)

    return Container(header, *sections, create_celebration_modal(), cls="space-y-8")



@rt
def index(): 
    card = get()
    return Titled(card)

serve()


