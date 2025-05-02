from ursina import *
import random
import time

app = Ursina()

## Game Setup ##
# Player
player = Entity(model='cube', scale=(1, 1, 1), collider='box', visible=False)
player.position = Vec3(0, 0, 0)
player.speed = 5
player.jumping = False
player.y = 0

# Camera
camera.parent = player
camera.position = (0, 2, 0)  
camera.rotation = (0, 0, 0)  

# Floor
floor_segments = []
for i in range(200):  
    z_pos = i * 5
    segment = Entity(
        model='cube',
        color=color.dark_gray,
        scale=(10, 1, 5),
        position=(0, -3, z_pos),
        collider='box'
    )
    floor_segments.append(segment)

# Tunnel
tunnel_segments = []
for i in range(200):  
    ring = Entity(
        model='cylinder',
        color=color.green,
        scale=(10, 1, 10),
        position=(0, 0, i * 5),
        rotation=(90, 0, 0),
        double_sided=True
    )
    tunnel_segments.append(ring)

# Skybox
Sky(color=color.gray)

# Lighting
DirectionalLight().look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgba(100, 100, 100, 0.8))

## State Variables ##
available_numbers = [str(i) for i in range(1, 10)]  

# Jump
jump_triggers = []
for i in range(20):  
    position = 50 + i * 50 + random.randint(-10, 10)
    jump_triggers.append(position)

next_trigger_index = 0
jump_required = False
jump_start_time = 0
REACTION_TIME_LIMIT = 0.8 

last_quiz_time = 0
quiz_interval = 20  
awaiting_answer = False
correct_option = None

## UI Elements ##
jump_prompt = Text(text="JUMP NOW!", scale=3, color=color.red, origin=(0,0), y=0.3, enabled=False)
correct_text = Text(text="CORRECT!", scale=3, color=color.green, origin=(0,0), y=0.3, enabled=False)
game_over_text = Text(text="GAME OVER!", scale=5, color=color.red, origin=(0,0), y=0, enabled=False)

number_display = Text(text='', scale=4, color=color.yellow, origin=(0,0), y=0.3, enabled=False)
question_display = Text(text='', scale=2, color=color.white, origin=(0,0), y=0.1, enabled=False)

# Counter
sequence_counter = 0
max_sequence = 3
current_sequence = []
number_display_duration = 1.5  

## Game Functions ##
def flash_number():
    global sequence_counter, current_sequence
    
    if sequence_counter < max_sequence:
        available = [n for n in available_numbers if n not in current_sequence]
        if available:  
            number = random.choice(available)
            current_sequence.append(number)
            
            number_display.text = number
            number_display.enabled = True
            sequence_counter += 1
            
            invoke(lambda: setattr(number_display, 'enabled', False), delay=number_display_duration)
            
            if sequence_counter < max_sequence:
                invoke(flash_number, delay=2)

def ask_memory_question():
    global awaiting_answer, correct_option, current_sequence
    
    if len(current_sequence) < 3:
        return  
    
    # Number picker (1st, 2nd, or 3rd)
    position = random.randint(0, 2)
    correct_option = current_sequence[position]
    
    # Number picker ask
    question_text = f'Which number appeared {["first", "second", "third"][position]}?'
    question_display.text = question_text
    question_display.enabled = True
    
    awaiting_answer = True

def clear_question():
    question_display.enabled = False

def show_correct():
    correct_text.enabled = True
    invoke(lambda: setattr(correct_text, 'enabled', False), delay=2)

def game_over(reason):
    game_over_text.text = f"GAME OVER!\n{reason}"
    game_over_text.enabled = True
    player.speed = 0  
    invoke(application.quit, delay=3)  

## Update Loop ##
def update():
    global jump_required, awaiting_answer, jump_start_time
    global sequence_counter, current_sequence, next_trigger_index
    
    # Constant speed (regardless of jump)
    player.position += Vec3(0, 0, player.speed * time.dt)
    
    if player.jumping:
        if player.y < 3:  
            player.y += 20 * time.dt  
        else:
            player.jumping = False
    elif player.y > 0:  
        player.y -= 20 * time.dt  
        if player.y < 0:
            player.y = 0
    
    player_z = player.position.z
    
    if next_trigger_index < len(jump_triggers):
        if player_z >= jump_triggers[next_trigger_index] and not jump_required:
            jump_required = True
            jump_prompt.enabled = True
            jump_start_time = time.time()
            next_trigger_index += 1
    
    # Jump check
    if jump_required:
        if time.time() - jump_start_time > REACTION_TIME_LIMIT:
            game_over("You didn't jump in time!")
    
    # Numbers between jumps
    if next_trigger_index > 0 and next_trigger_index < len(jump_triggers):
        current_trigger = jump_triggers[next_trigger_index-1]
        next_trigger = jump_triggers[next_trigger_index]
        
        # Numbers between jump prompts
        mid_point = current_trigger + (next_trigger - current_trigger) / 2
        
        if sequence_counter == 0 and not jump_required and abs(player_z - mid_point) < 5:
            sequence_counter = 0
            current_sequence = []
            flash_number()
    
    current_time = time.time()
    if not awaiting_answer and current_time - last_quiz_time > quiz_interval and sequence_counter == max_sequence:
        ask_memory_question()

## Input Handler ##
def input(key):
    global jump_required, awaiting_answer, last_quiz_time
    global sequence_counter, jump_start_time
    
    if key == 'escape':
        application.quit()
    
    # Jump
    if key == 'space':
        if jump_required:
            # Check if jumped
            reaction_time = time.time() - jump_start_time
            if reaction_time <= REACTION_TIME_LIMIT:
                jump_required = False
                jump_prompt.enabled = False
        
        player.jumping = True
    
    # Answer
    if awaiting_answer and key in available_numbers:
        if key == correct_option:
            show_correct()
            clear_question()
            awaiting_answer = False
            last_quiz_time = time.time()
            sequence_counter = 0  
        else:
            game_over("Wrong answer!")

## Help Text ##
help_text = Text(
    text="Press SPACE to jump when prompted\nPress number keys to answer questions\nESC to quit",
    scale=1.5,
    position=(-0.85, 0.45),
    color=color.white
)

app.run()