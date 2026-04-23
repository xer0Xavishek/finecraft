from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# =============================================================================
# GAME ENGINE VARIABLES
# =============================================================================

# Window (Fixed to 1280x720)
WINDOW_W = 1920
WINDOW_H = 1080
fovY     = 90

# Player / Camera
player_pos  = [0.0, -80.0, 50.0]   # X, Y, Z (Z is strictly the FEET)
yaw         = 90.0                   
pitch       = -15.0                  
camera_mode = "FirstPerson"        # "FirstPerson" or "ThirdPerson"

# Constants
EYE_HEIGHT  = 34.0                 # Adjusted to match the new 3D model's head
BLOCK_SIZE  = 25                   # World-units per block
BLOCK_HALF  = BLOCK_SIZE / 2.0

# Mouse state
last_mouse_x = WINDOW_W // 2
last_mouse_y = WINDOW_H // 2
mouse_sensitivity = 0.18

# Voxel world
world_blocks = {}           # (ix, iy, iz) -> (r, g, b)

# Held block colour (cycles with keys 1-5)
PALETTE = [
    (0.55, 0.27, 0.07),     # 1  Wood / dirt brown
    (0.25, 0.70, 0.25),     # 2  Grass green
    (0.55, 0.55, 0.55),     # 3  Stone grey
    (0.90, 0.80, 0.20),     # 4  Sand / gold
    (0.25, 0.55, 0.90),     # 5  Water / ice blue
]
held_color_index = 0

# HUD / state
score        = 0            
blocks_placed = 0
game_mode    = "Survival"   
cheat_mode   = False        
show_help    = True

# Gravity / jumping (Adjusted for snappy Minecraft feel)
vel_z        = 0.0
GRAVITY      = -0.8
JUMP_VEL     = 8.0
on_ground    = False

# =============================================================================
# WORLD GENERATION
# =============================================================================

def _set(ix, iy, iz, color):
    world_blocks[(ix, iy, iz)] = color

def init_world():
    random.seed(42)
    # Flat grass base layer
    for ix in range(-14, 15):
        for iy in range(-14, 15):
            _set(ix, iy, 0, (0.22, 0.68, 0.22))        
            _set(ix, iy, -1, (0.45, 0.30, 0.15))       
            for iz in [-2, -3]:
                _set(ix, iy, iz, (0.50, 0.50, 0.50))

    # Small hills
    for _ in range(10):
        cx = random.randint(-10, 10)
        cy = random.randint(-10, 10)
        for ix in range(cx-2, cx+3):
            for iy in range(cy-2, cy+3):
                if abs(ix-cx) + abs(iy-cy) <= 3:
                    _set(ix, iy, 1, (0.22, 0.68, 0.22))
                    if abs(ix-cx) + abs(iy-cy) <= 1:
                        _set(ix, iy, 2, (0.22, 0.68, 0.22))

    # Path
    for iy in range(-14, 15):
        _set(0, iy, 0, (0.60, 0.45, 0.25))
        _set(1, iy, 0, (0.60, 0.45, 0.25))

    # Trees
    tree_spots = [(-6, -6), (6, -8), (-8, 5), (5, 6), (-3, 10), (10, -3), (-11, 2), (3, -11)]
    for tx, ty in tree_spots:
        if (tx, ty, 0) in world_blocks:
            for iz in range(1, 4): _set(tx, ty, iz, (0.36, 0.20, 0.08))
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    for dz in [4, 5]:
                        if abs(dx) + abs(dy) <= 3: _set(tx+dx, ty+dy, dz, (0.10, 0.50, 0.10))
            _set(tx, ty, 6, (0.10, 0.50, 0.10))

init_world()

# =============================================================================
# UTILITY HELPERS
# =============================================================================

def get_voxel(x, y, z):
    bx = math.floor((x + BLOCK_HALF) / BLOCK_SIZE)
    by = math.floor((y + BLOCK_HALF) / BLOCK_SIZE)
    bz = math.floor((z + BLOCK_HALF) / BLOCK_SIZE)
    return (bx, by, bz)

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
        cx += dx * step
        cy += dy * step
        cz += dz * step
    return None, None

def try_move(dx, dy):
    if game_mode == "Creative":
        player_pos[0] += dx
        player_pos[1] += dy
        return

    # Check X-axis collision
    new_x = player_pos[0] + dx
    bx, by, _ = get_voxel(new_x, player_pos[1], player_pos[2])
    _, _, bz_foot = get_voxel(new_x, player_pos[1], player_pos[2] + 1.0)
    _, _, bz_head = get_voxel(new_x, player_pos[1], player_pos[2] + EYE_HEIGHT - 2.0)
    
    if (bx, by, bz_foot) not in world_blocks and (bx, by, bz_head) not in world_blocks:
        player_pos[0] = new_x

    # Check Y-axis collision
    new_y = player_pos[1] + dy
    bx, by, _ = get_voxel(player_pos[0], new_y, player_pos[2])
    
    if (bx, by, bz_foot) not in world_blocks and (bx, by, bz_head) not in world_blocks:
        player_pos[1] = new_y

# =============================================================================
# DRAWING PRIMITIVES
# =============================================================================

def draw_cube_unit():
    """Helper purely for drawing the player model parts."""
    s = 0.5
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0); glVertex3f(-s,s,-s); glVertex3f(s,s,-s); glVertex3f(s,s,s); glVertex3f(-s,s,s)
    glNormal3f(0, -1, 0); glVertex3f(-s,-s,s); glVertex3f(s,-s,s); glVertex3f(s,-s,-s); glVertex3f(-s,-s,-s)
    glNormal3f(1, 0, 0); glVertex3f(s,-s,s); glVertex3f(s,s,s); glVertex3f(s,s,-s); glVertex3f(s,-s,-s)
    glNormal3f(-1, 0, 0); glVertex3f(-s,-s,-s); glVertex3f(-s,s,-s); glVertex3f(-s,s,s); glVertex3f(-s,-s,s)
    glNormal3f(0, 0, 1); glVertex3f(-s,-s,s); glVertex3f(s,-s,s); glVertex3f(s,s,s); glVertex3f(-s,s,s)
    glNormal3f(0, 0, -1); glVertex3f(-s,-s,-s); glVertex3f(s,-s,-s); glVertex3f(s,s,-s); glVertex3f(-s,s,-s)
    glEnd()

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

def draw_player_model():
    """Renders a full Minecraft-style 3D avatar with animated walking."""
    if camera_mode != "ThirdPerson": return

    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(yaw - 90, 0, 0, 1) # Align body to camera

    skin = (0.9, 0.75, 0.6)
    shirt = (0.2, 0.6, 0.6)   # Cyan shirt (like Steve)
    pants = (0.2, 0.2, 0.7)   # Blue pants

    scale = 1.15
    
    # Calculate a swing variable based on movement distance for walking animation
    walk_cycle = (player_pos[0] + player_pos[1]) * 0.2
    swing = math.sin(walk_cycle) * 35.0 if on_ground else 0.0

    # 1. Left Leg
    glPushMatrix()
    glColor3f(*pants)
    glTranslatef(-2.5 * scale, 0, 6 * scale)
    glRotatef(swing, 1, 0, 0) # Swing forward/back
    glScalef(4 * scale, 4 * scale, 12 * scale)
    draw_cube_unit()
    glPopMatrix()

    # 2. Right Leg
    glPushMatrix()
    glColor3f(*pants)
    glTranslatef(2.5 * scale, 0, 6 * scale)
    glRotatef(-swing, 1, 0, 0) # Opposite swing
    glScalef(4 * scale, 4 * scale, 12 * scale)
    draw_cube_unit()
    glPopMatrix()

    # 3. Torso
    glPushMatrix()
    glColor3f(*shirt)
    glTranslatef(0, 0, 18 * scale)
    glScalef(9 * scale, 4 * scale, 12 * scale)
    draw_cube_unit()
    glPopMatrix()

    # 4. Left Arm
    glPushMatrix()
    glColor3f(*skin)
    glTranslatef(-6.5 * scale, 0, 18 * scale)
    glRotatef(-swing, 1, 0, 0) # Arms swing opposite to legs
    glScalef(4 * scale, 4 * scale, 12 * scale)
    draw_cube_unit()
    glPopMatrix()

    # 5. Right Arm
    glPushMatrix()
    glColor3f(*skin)
    glTranslatef(6.5 * scale, 0, 18 * scale)
    glRotatef(swing, 1, 0, 0)
    glScalef(4 * scale, 4 * scale, 12 * scale)
    draw_cube_unit()
    glPopMatrix()

    # 6. Head
    glPushMatrix()
    glColor3f(*skin)
    glTranslatef(0, 0, 28 * scale)
    # The head pitches up and down to match mouse view
    glRotatef(pitch, 1, 0, 0) 
    glRotatef(90, 0, 0, 1) # Fix face forward
    glScalef(8 * scale, 8 * scale, 8 * scale)
    draw_cube_unit()
    glPopMatrix()

    glPopMatrix()

# =============================================================================
# WORLD RENDER (ULTRA OPTIMIZED)
# =============================================================================

def draw_shapes():
    """Batched Rendering System - Eliminates Python loop lag for smooth 60 FPS."""
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [200.0, 200.0, 400.0, 0.0])

    s = BLOCK_HALF
    
    # ONE single PyOpenGL call to the graphics card to draw the entire map
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
        
        # Manually unrolling vertices removes the lag caused by glPushMatrix()
        if f_posY: 
            glNormal3f(0, 1, 0)
            glVertex3f(x-s, y+s, z-s); glVertex3f(x+s, y+s, z-s); glVertex3f(x+s, y+s, z+s); glVertex3f(x-s, y+s, z+s)
        if f_negY:
            glNormal3f(0, -1, 0)
            glVertex3f(x-s, y-s, z+s); glVertex3f(x+s, y-s, z+s); glVertex3f(x+s, y-s, z-s); glVertex3f(x-s, y-s, z-s)
        if f_posX:
            glNormal3f(1, 0, 0)
            glVertex3f(x+s, y-s, z+s); glVertex3f(x+s, y+s, z+s); glVertex3f(x+s, y+s, z-s); glVertex3f(x+s, y-s, z-s)
        if f_negX:
            glNormal3f(-1, 0, 0)
            glVertex3f(x-s, y-s, z-s); glVertex3f(x-s, y+s, z-s); glVertex3f(x-s, y+s, z+s); glVertex3f(x-s, y-s, z+s)
        if f_posZ:
            glNormal3f(0, 0, 1)
            glVertex3f(x-s, y-s, z+s); glVertex3f(x+s, y-s, z+s); glVertex3f(x+s, y+s, z+s); glVertex3f(x-s, y+s, z+s)
        if f_negZ:
            glNormal3f(0, 0, -1)
            glVertex3f(x-s, y-s, z-s); glVertex3f(x+s, y-s, z-s); glVertex3f(x+s, y+s, z-s); glVertex3f(x-s, y+s, z-s)
            
    glEnd()

    draw_player_model()
    glDisable(GL_LIGHTING)

# =============================================================================
# INPUT HANDLERS
# =============================================================================

def keyboardListener(key, x, y):
    global held_color_index, game_mode, cheat_mode, show_help, camera_mode
    global vel_z, score, blocks_placed

    speed = 10.0 if game_mode == "Creative" else 6.0
    ry = math.radians(yaw)
    fx, fy = math.cos(ry), math.sin(ry)
    rx, ry2 = math.sin(ry), -math.cos(ry)

    if key == b'w': try_move(fx * speed, fy * speed)
    if key == b's': try_move(-fx * speed, -fy * speed)
    if key == b'a': try_move(-rx * speed, -ry2 * speed)
    if key == b'd': try_move(rx * speed, ry2 * speed)

    if key == b' ': 
        if game_mode == "Creative": player_pos[2] += speed
        elif on_ground: vel_z = JUMP_VEL
    if key == b'x': 
        if game_mode == "Creative": player_pos[2] -= speed

    if key == b'v': camera_mode = "ThirdPerson" if camera_mode == "FirstPerson" else "FirstPerson"
    if key == b'g': game_mode = "Creative" if game_mode == "Survival" else "Survival"; vel_z = 0.0
    
    if key == b'1': held_color_index = 0
    if key == b'2': held_color_index = 1
    if key == b'3': held_color_index = 2
    if key == b'4': held_color_index = 3
    if key == b'5': held_color_index = 4

    if key == b'c': cheat_mode = not cheat_mode
    if key == b'h': show_help = not show_help
    if key == b'\x1b': import sys; sys.exit(0)


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
    if button == GLUT_LEFT_BUTTON and hit and hit[2] >= 0:
        del world_blocks[hit]; score += 1
    if button == GLUT_RIGHT_BUTTON and hit and prev:
        world_blocks[prev] = PALETTE[held_color_index]; blocks_placed += 1

# =============================================================================
# PHYSICS
# =============================================================================

def apply_physics():
    global vel_z, on_ground
    if game_mode != "Survival": on_ground = False; return

    vel_z += GRAVITY         
    next_z = player_pos[2] + vel_z

    bx, by, bz_under = get_voxel(player_pos[0], player_pos[1], next_z - 0.1)
    block_top = (bz_under * BLOCK_SIZE) + BLOCK_HALF

    if (bx, by, bz_under) in world_blocks and next_z <= block_top:
        player_pos[2] = block_top
        vel_z = 0.0
        on_ground = True
    else:
        player_pos[2] = next_z
        on_ground = False

    if player_pos[2] < -200: player_pos[2] = 100.0; vel_z = 0.0

# =============================================================================
# CAMERA
# =============================================================================

def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(fovY, WINDOW_W / WINDOW_H, 0.5, 2000)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    ry, rp = math.radians(yaw), math.radians(pitch)
    dir_x, dir_y, dir_z = math.cos(ry)*math.cos(rp), math.sin(ry)*math.cos(rp), math.sin(rp)
    
    eye_x, eye_y, eye_z = player_pos[0], player_pos[1], player_pos[2] + EYE_HEIGHT

    if camera_mode == "ThirdPerson":
        dist = 120.0
        cam_x = eye_x - dir_x * dist
        cam_y = eye_y - dir_y * dist
        cam_z = eye_z - dir_z * dist
        gluLookAt(cam_x, cam_y, cam_z, eye_x, eye_y, eye_z, 0, 0, 1)
    else:
        gluLookAt(eye_x, eye_y, eye_z, eye_x + dir_x, eye_y + dir_y, eye_z + dir_z, 0, 0, 1)

# =============================================================================
# HUD OVERLAY
# =============================================================================

def draw_hud():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)

    if camera_mode == "FirstPerson": draw_crosshair()

    draw_text(12, WINDOW_H - 26,  f"Camera: {camera_mode} | Mode: {game_mode}", GLUT_BITMAP_HELVETICA_18)
    draw_text(12, WINDOW_H - 50,  f"Blocks Broken : {score}", GLUT_BITMAP_HELVETICA_18)
    pname = ["Brown","Green","Stone","Sand","Blue"][held_color_index]
    draw_text(12, WINDOW_H - 74, f"Held : [{held_color_index+1}] {pname}", GLUT_BITMAP_HELVETICA_18)

    if show_help:
        hy = 140
        draw_text(WINDOW_W - 290, hy,      "[ Controls ]", GLUT_BITMAP_HELVETICA_18)
        draw_text(WINDOW_W - 290, hy - 24, "W/A/S/D  - Move", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 40, "SPACE    - Jump", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 56, "V        - Toggle Camera", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 72, "LMB/RMB  - Break/Place", GLUT_BITMAP_HELVETICA_12)
        draw_text(WINDOW_W - 290, hy - 88, "G        - Toggle God Mode", GLUT_BITMAP_HELVETICA_12)

    glEnable(GL_DEPTH_TEST); glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# =============================================================================
# GLUT LIFECYCLE
# =============================================================================

def idle(): apply_physics(); glutPostRedisplay()

def showScreen():
    glClearColor(0.52, 0.74, 0.94, 1.0)
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
    glutCreateWindow(b"Minecraft Clone V5 - Smooth & Animated")
    glutDisplayFunc(showScreen); glutKeyboardFunc(keyboardListener); glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener); glutPassiveMotionFunc(passiveMouseListener); glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__": main()