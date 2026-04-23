from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import time # Added for FPS capping

# =============================================================================
# GAME ENGINE VARIABLES
# =============================================================================

WINDOW_W = 1920
WINDOW_H = 1080
fovY     = 90

# Player / Camera
player_pos  = [0.0, -80.0, 300.0]   
yaw         = 90.0                   
pitch       = -15.0                  
camera_mode = "FirstPerson"        

# Constants
EYE_HEIGHT  = 34.0                 
BLOCK_SIZE  = 25                   
BLOCK_HALF  = BLOCK_SIZE / 2.0

# Mouse & Keyboard State
last_mouse_x = WINDOW_W // 2
last_mouse_y = WINDOW_H // 2
mouse_sensitivity = 0.18

# Tracks which keys are currently being held down
key_states = {b'w': False, b's': False, b'a': False, b'd': False, b' ': False, b'x': False}

# Voxel world
world_blocks = {}           
world_display_list = None   

# Block Colors
C_WOOD  = (0.55, 0.27, 0.07)
C_GRASS = (0.25, 0.70, 0.25)
C_STONE = (0.50, 0.50, 0.50)
C_GOLD  = (0.90, 0.80, 0.20)
C_WATER = (0.25, 0.55, 0.90)
C_LEAF  = (0.10, 0.50, 0.10)
C_CLOUD = (0.95, 0.95, 0.95)
C_DIRT  = (0.45, 0.30, 0.15)

PALETTE = [C_WOOD, C_GRASS, C_STONE, C_GOLD, C_WATER]
held_color_index = 0

# HUD / state
score        = 0            
blocks_placed = 0
game_mode    = "Survival"   # Changed default back to survival so you can test movement
cheat_mode   = False        
show_help    = True

# Environment Toggles
day_time = True
rain_mode = False

rain_particles = []
for _ in range(500):
    rain_particles.append([random.uniform(-800, 800), random.uniform(-800, 800), random.uniform(0, 800), random.uniform(15, 25)])

# Physics & Timing
vel_z          = 0.0
GRAVITY        = -0.6
JUMP_VEL       = 8.0
on_ground      = False
last_frame_time = time.time() # Used to lock FPS to 60

# =============================================================================
# ADVANCED WORLD GENERATION & OPTIMIZATION
# =============================================================================

def _set(ix, iy, iz, color):
    world_blocks[(ix, iy, iz)] = color
s
def build_world_list():
    global world_display_list
    if world_display_list is None:
        world_display_list = glGenLists(1)
    
    glNewList(world_display_list, GL_COMPILE)
    s = BLOCK_HALF
    glBegin(GL_QUADS)
    for (ix, iy, iz), color in world_blocks.items():
        f_posY = (ix, iy+1, iz) not in world_blocks
        f_negY = (ix, iy-1, iz) not in world_blocks
        f_posX = (ix+1, iy, iz) not in world_blocks
        f_negX = (ix-1, iy, iz) not in world_blocks
        f_posZ = (ix, iy, iz+1) not in world_blocks
        f_negZ = (ix, iy, iz-1) not in world_blocks
        
        if not (f_posY or f_negY or f_posX or f_negX or f_posZ or f_negZ): continue
            
        glColor3f(*color)
        x, y, z = ix * BLOCK_SIZE, iy * BLOCK_SIZE, iz * BLOCK_SIZE
        
        if f_posY: glNormal3f(0, 1, 0); glVertex3f(x-s, y+s, z-s); glVertex3f(x+s, y+s, z-s); glVertex3f(x+s, y+s, z+s); glVertex3f(x-s, y+s, z+s)
        if f_negY: glNormal3f(0, -1, 0); glVertex3f(x-s, y-s, z+s); glVertex3f(x+s, y-s, z+s); glVertex3f(x+s, y-s, z-s); glVertex3f(x-s, y-s, z-s)
        if f_posX: glNormal3f(1, 0, 0); glVertex3f(x+s, y-s, z+s); glVertex3f(x+s, y+s, z+s); glVertex3f(x+s, y+s, z-s); glVertex3f(x+s, y-s, z-s)
        if f_negX: glNormal3f(-1, 0, 0); glVertex3f(x-s, y-s, z-s); glVertex3f(x-s, y+s, z-s); glVertex3f(x-s, y+s, z+s); glVertex3f(x-s, y-s, z+s)
        if f_posZ: glNormal3f(0, 0, 1); glVertex3f(x-s, y-s, z+s); glVertex3f(x+s, y-s, z+s); glVertex3f(x+s, y+s, z+s); glVertex3f(x-s, y+s, z+s)
        if f_negZ: glNormal3f(0, 0, -1); glVertex3f(x-s, y-s, z-s); glVertex3f(x+s, y-s, z-s); glVertex3f(x+s, y+s, z-s); glVertex3f(x-s, y+s, z-s)
    glEnd()
    glEndList()

def init_world():
    random.seed(101) 
    for ix in range(-25, 26):
        for iy in range(-25, 26):
            h = int(math.sin(ix * 0.15) * 4 + math.cos(iy * 0.2) * 3 + math.sin((ix+iy) * 0.1) * 2)
            for iz in range(-10, h): _set(ix, iy, iz, C_STONE)
            if h < -1:
                _set(ix, iy, h, C_DIRT)
                for w_z in range(h + 1, 0): _set(ix, iy, w_z, C_WATER)
            elif h > 4: _set(ix, iy, h, C_STONE)
            else:
                _set(ix, iy, h, C_GRASS); _set(ix, iy, h-1, C_DIRT)

            if -1 <= h <= 4 and random.random() < 0.03:
                for tz in range(1, 4): _set(ix, iy, h + tz, C_WOOD) 
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        for dz in [3, 4]:
                            if abs(dx) + abs(dy) <= 2: _set(ix+dx, iy+dy, h+dz, C_LEAF)

    for _ in range(15):
        cx, cy = random.randint(-25, 25), random.randint(-25, 25)
        cz = random.randint(18, 22)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if random.random() > 0.2: _set(cx+dx, cy+dy, cz, C_CLOUD)

    for _ in range(12):
        cx, cy, cz = random.randint(-20, 20), random.randint(-20, 20), random.randint(-8, -3)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                for dz in range(-3, 4):
                    if dx*dx + dy*dy + dz*dz <= 9: 
                        pos = (cx+dx, cy+dy, cz+dz)
                        if pos in world_blocks: del world_blocks[pos]
                        if random.random() < 0.05 and dz == -2: _set(cx+dx, cy+dy, cz+dz, C_GOLD)

    bx, by, bz = 0, 0, int(math.sin(0) * 4 + math.cos(0) * 3 + math.sin(0) * 2) + 1
    if bz <= 0: bz = 1 
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            for dz in range(0, 4):
                if dx == -3 or dx == 3 or dy == -3 or dy == 3: _set(bx+dx, by+dy, bz+dz, C_WOOD)
                if dz == 0 or dz == 3: _set(bx+dx, by+dy, bz+dz, C_WOOD)
    for dz in range(0, 2): _set(bx, by-3, bz+dz, C_WOOD); del world_blocks[(bx, by-3, bz+dz)]

    build_world_list()

# =============================================================================
# UTILITIES & PHYSICS
# =============================================================================

def get_voxel(x, y, z):
    return (math.floor((x + BLOCK_HALF) / BLOCK_SIZE), 
            math.floor((y + BLOCK_HALF) / BLOCK_SIZE), 
            math.floor((z + BLOCK_HALF) / BLOCK_SIZE))

def _look_dir():
    ry, rp = math.radians(yaw), math.radians(pitch)
    return (math.cos(ry) * math.cos(rp), math.sin(ry) * math.cos(rp), math.sin(rp))

def _raycast(steps=120, reach=200.0):
    dx, dy, dz = _look_dir()
    step = reach / steps
    cx, cy, cz = player_pos[0], player_pos[1], player_pos[2] + EYE_HEIGHT
    prev = None
    for _ in range(steps):
        key = get_voxel(cx, cy, cz)
        if key in world_blocks: return key, prev
        prev = key
        cx += dx * step; cy += dy * step; cz += dz * step
    return None, None

def try_move(dx, dy):
    if game_mode == "Creative":
        player_pos[0] += dx; player_pos[1] += dy
        return
    new_x = player_pos[0] + dx
    bx, by, _ = get_voxel(new_x, player_pos[1], player_pos[2])
    _, _, bz_foot = get_voxel(new_x, player_pos[1], player_pos[2] + 1.0)
    _, _, bz_head = get_voxel(new_x, player_pos[1], player_pos[2] + EYE_HEIGHT - 2.0)
    if (bx, by, bz_foot) not in world_blocks and (bx, by, bz_head) not in world_blocks:
        player_pos[0] = new_x
    new_y = player_pos[1] + dy
    bx, by, _ = get_voxel(player_pos[0], new_y, player_pos[2])
    if (bx, by, bz_foot) not in world_blocks and (bx, by, bz_head) not in world_blocks:
        player_pos[1] = new_y

def apply_physics():
    global vel_z, on_ground, player_pos
    
    # 1. Handle Smooth Continuous Movement based on keys held down
    speed = 2.0 if game_mode == "Survival" else 8.0
    ry = math.radians(yaw)
    fx, fy = math.cos(ry), math.sin(ry)
    rx, ry2 = math.sin(ry), -math.cos(ry)

    if key_states[b'w']: try_move(fx * speed, fy * speed)
    if key_states[b's']: try_move(-fx * speed, -fy * speed)
    if key_states[b'a']: try_move(-rx * speed, -ry2 * speed)
    if key_states[b'd']: try_move(rx * speed, ry2 * speed)

    if key_states[b' ']: 
        if game_mode == "Creative": player_pos[2] += speed
        elif on_ground: vel_z = JUMP_VEL
    if key_states[b'x']: 
        if game_mode == "Creative": player_pos[2] -= speed

    # 2. Handle Gravity & Floor Collisions
    if game_mode != "Survival": 
        on_ground = False
        return
        
    vel_z += GRAVITY         
    next_z = player_pos[2] + vel_z
    bx, by, bz_under = get_voxel(player_pos[0], player_pos[1], next_z - 0.1)
    block_top = (bz_under * BLOCK_SIZE) + BLOCK_HALF
    if (bx, by, bz_under) in world_blocks and next_z <= block_top:
        player_pos[2] = block_top
        vel_z = 0.0; on_ground = True
    else:
        player_pos[2] = next_z; on_ground = False
        
    if player_pos[2] < -200: player_pos[2] = 300.0; vel_z = 0.0

# =============================================================================
# ENVIRONMENT RENDERERS
# =============================================================================

def draw_cube_unit():
    s = 0.5
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0); glVertex3f(-s,s,-s); glVertex3f(s,s,-s); glVertex3f(s,s,s); glVertex3f(-s,s,s)
    glNormal3f(0, -1, 0); glVertex3f(-s,-s,s); glVertex3f(s,-s,s); glVertex3f(s,-s,-s); glVertex3f(-s,-s,-s)
    glNormal3f(1, 0, 0); glVertex3f(s,-s,s); glVertex3f(s,s,s); glVertex3f(s,s,-s); glVertex3f(s,-s,-s)
    glNormal3f(-1, 0, 0); glVertex3f(-s,-s,-s); glVertex3f(-s,s,-s); glVertex3f(-s,s,s); glVertex3f(-s,-s,s)
    glNormal3f(0, 0, 1); glVertex3f(-s,-s,s); glVertex3f(s,-s,s); glVertex3f(s,s,s); glVertex3f(-s,s,s)
    glNormal3f(0, 0, -1); glVertex3f(-s,-s,-s); glVertex3f(s,-s,-s); glVertex3f(s,s,-s); glVertex3f(-s,s,-s)
    glEnd()

def draw_celestial_body():
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(player_pos[0] - 200, player_pos[1] + 300, 600.0)
    glScalef(60, 60, 60)
    if day_time: glColor3f(1.0, 1.0, 0.2)
    else: glColor3f(0.8, 0.8, 0.9)
    draw_cube_unit()
    glPopMatrix()
    glEnable(GL_LIGHTING)

def update_and_draw_rain():
    if not rain_mode: return
    glDisable(GL_LIGHTING)
    glColor3f(0.4, 0.6, 0.9)
    glLineWidth(2)
    glBegin(GL_LINES)
    for p in rain_particles:
        p[2] -= p[3]
        if p[2] < -100:
            p[0] = player_pos[0] + random.uniform(-600, 600)
            p[1] = player_pos[1] + random.uniform(-600, 600)
            p[2] = player_pos[2] + random.uniform(400, 800)
        glVertex3f(p[0], p[1], p[2])
        glVertex3f(p[0], p[1], p[2] + 25)
    glEnd()
    glLineWidth(1)
    glEnable(GL_LIGHTING)

def draw_player():
    if camera_mode == "FirstPerson": return
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2] + 15)
    glRotatef(yaw - 90, 0, 0, 1) 
    
    glPushMatrix() # Head
    glTranslatef(0, 0, 16)
    glColor3f(0.9, 0.7, 0.6) 
    glScalef(12, 12, 12)
    draw_cube_unit()
    glPopMatrix()

    glPushMatrix() # Body
    glColor3f(0.0, 0.6, 0.6)
    glScalef(14, 8, 20)
    draw_cube_unit()
    glPopMatrix()

    glPopMatrix()
    glEnable(GL_LIGHTING)

# =============================================================================
# MAIN WORLD RENDER
# =============================================================================

def draw_shapes():
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    if day_time:
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    else:
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.15, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.2, 0.2, 0.3, 1.0])
        
    glLightfv(GL_LIGHT0, GL_POSITION, [200.0, 200.0, 400.0, 0.0])

    if world_display_list is not None:
        glCallList(world_display_list)

    draw_celestial_body()
    update_and_draw_rain()
    draw_player()
    
    glDisable(GL_LIGHTING)

# =============================================================================
# INPUT HANDLERS
# =============================================================================

def keyboardListener(key, x, y):
    """Triggers when a key is PRESSED DOWN."""
    global held_color_index, game_mode, cheat_mode, show_help, camera_mode, day_time, rain_mode
    
    k = key.lower()
    if k in key_states:
        key_states[k] = True

    # Single-press toggle keys
    if k == b'v': camera_mode = "ThirdPerson" if camera_mode == "FirstPerson" else "FirstPerson"
    if k == b'g': game_mode = "Creative" if game_mode == "Survival" else "Survival"; vel_z = 0.0
    if k == b'n': day_time = not day_time
    if k == b'r': rain_mode = not rain_mode
    if k == b'1': held_color_index = 0
    if k == b'2': held_color_index = 1
    if k == b'3': held_color_index = 2
    if k == b'4': held_color_index = 3
    if k == b'5': held_color_index = 4
    if k == b'c': cheat_mode = not cheat_mode
    if k == b'h': show_help = not show_help
    if k == b'\x1b': sys.exit(0)

def keyboardUpListener(key, x, y):
    """Triggers when a key is LIFTED UP."""
    k = key.lower()
    if k in key_states:
        key_states[k] = False

def specialKeyListener(key, x, y): pass

def passiveMouseListener(x, y):
    global yaw, pitch, last_mouse_x, last_mouse_y
    yaw   -= (x - last_mouse_x) * mouse_sensitivity 
    pitch -= (y - last_mouse_y) * mouse_sensitivity
    pitch  = max(-89.0, min(89.0, pitch))
    last_mouse_x, last_mouse_y = x, y

def mouseListener(button, state, x, y):
    global score, blocks_placed
    if state != GLUT_DOWN: return
    hit, prev = _raycast()
    if button == GLUT_LEFT_BUTTON and hit:
        del world_blocks[hit]
        score += 1
        build_world_list()
    if button == GLUT_RIGHT_BUTTON and hit and prev:
        world_blocks[prev] = PALETTE[held_color_index]
        blocks_placed += 1
        build_world_list()

# =============================================================================
# CAMERA & HUD
# =============================================================================

def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(fovY, WINDOW_W / WINDOW_H, 0.5, 3000)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    ry, rp = math.radians(yaw), math.radians(pitch)
    dir_x, dir_y, dir_z = math.cos(ry)*math.cos(rp), math.sin(ry)*math.cos(rp), math.sin(rp)
    eye_x, eye_y, eye_z = player_pos[0], player_pos[1], player_pos[2] + EYE_HEIGHT

    if camera_mode == "ThirdPerson":
        dist = 120.0
        gluLookAt(eye_x - dir_x * dist, eye_y - dir_y * dist, eye_z - dir_z * dist, eye_x, eye_y, eye_z, 0, 0, 1)
    else:
        gluLookAt(eye_x, eye_y, eye_z, eye_x + dir_x, eye_y + dir_y, eye_z + dir_z, 0, 0, 1)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text: glutBitmapCharacter(font, ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_crosshair():
    cx, cy = WINDOW_W / 2, WINDOW_H / 2
    glColor3f(1, 1, 1); glLineWidth(2); glBegin(GL_LINES)
    glVertex2f(cx - 10, cy); glVertex2f(cx + 10, cy)
    glVertex2f(cx, cy - 10); glVertex2f(cx, cy + 10)
    glEnd(); glLineWidth(1)

def draw_hud():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)

    if camera_mode == "FirstPerson": draw_crosshair()

    draw_text(12, WINDOW_H - 26,  f"Camera: {camera_mode} | Mode: {game_mode}", GLUT_BITMAP_HELVETICA_18)
    env = "Day" if day_time else "Night"
    wea = "Rain" if rain_mode else "Clear"
    draw_text(12, WINDOW_H - 50,  f"Time: {env} | Weather: {wea}", GLUT_BITMAP_HELVETICA_18)
    
    pname = ["Wood","Grass","Stone","Gold","Water"][held_color_index]
    draw_text(12, WINDOW_H - 74, f"Held : [{held_color_index+1}] {pname}", GLUT_BITMAP_HELVETICA_18)

    if show_help:
        hy = 160
        draw_text(WINDOW_W - 290, hy,      "[ Controls ]", GLUT_BITMAP_HELVETICA_18)
        draw_text(WINDOW_W - 290, hy - 24, "W/A/S/D  - Move", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 40, "SPACE/X  - Up/Down", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 56, "V        - Toggle Camera", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 72, "N        - Toggle Day/Night", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 88, "R        - Toggle Rain", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 104, "G        - Toggle Game Mode", GLUT_BITMAP_HELVETICA_12)

    glEnable(GL_DEPTH_TEST); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# =============================================================================
# GLUT LIFECYCLE
# =============================================================================

def idle():
    """60 FPS Frame Limiter to guarantee consistent movement speed on all PCs"""
    global last_frame_time
    current_time = time.time()
    
    if current_time - last_frame_time >= (1.0 / 60.0): # 60 Frames Per Second
        apply_physics()
        glutPostRedisplay()
        last_frame_time = current_time

def showScreen():
    if day_time:
        if rain_mode: glClearColor(0.4, 0.45, 0.5, 1.0)
        else: glClearColor(0.52, 0.74, 0.94, 1.0)       
    else:
        glClearColor(0.05, 0.05, 0.1, 1.0)              
        
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST) 
    glLoadIdentity(); glViewport(0, 0, WINDOW_W, WINDOW_H)

    setupCamera()
    draw_shapes()
    draw_hud()
    glutSwapBuffers()

def main():
    glutInit(); glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H); glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Minecraft Clone - Perfect Movement")
    
    init_world()
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    
    # Enable Keyboard UP function to track key releases smoothly
    try: glutKeyboardUpFunc(keyboardUpListener)
    except: pass
    
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutPassiveMotionFunc(passiveMouseListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__": main() 