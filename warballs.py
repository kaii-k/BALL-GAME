import pygame
import random
import math
import time

# --- setup ---
pygame.init()
WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
ARENA_RADIUS = 330
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Fight Arena")
clock = pygame.time.Clock()

# --- ball class ---
class Ball:
    def __init__(self, x, y, r, color, name):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.speed = 2
        self.angle = random.uniform(0, math.pi * 2)
        self.lines = []
        self.alive = True
        self.name = name

    def move(self):
        if not self.alive or self.speed == 0:
            return
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        dx, dy = self.x - CENTER[0], self.y - CENTER[1]
        dist = math.hypot(dx, dy)

        if dist + self.r >= ARENA_RADIUS:
            bx = CENTER[0] + dx / dist * ARENA_RADIUS
            by = CENTER[1] + dy / dist * ARENA_RADIUS
            self.lines.append((bx, by))
            self.speed += 0.3
            self.angle += math.pi + random.uniform(-0.3, 0.3)
            self.x = CENTER[0] + dx / dist * (ARENA_RADIUS - self.r - 1)
            self.y = CENTER[1] + dy / dist * (ARENA_RADIUS - self.r - 1)

    def draw(self):
        if self.alive:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.r)

    def check_collision(self, other):
        if not self.alive or not other.alive:
            return
        dx = self.x - other.x
        dy = self.y - other.y
        dist = math.hypot(dx, dy)

        if dist < self.r + other.r:
            self.angle += math.pi / 2
            other.angle -= math.pi / 2
            self.speed += 0.2
            other.speed += 0.2

# --- helper ---
def line_intersects_circle(p1, p2, ball):
    if not ball.alive:
        return False
    x0, y0 = ball.x, ball.y
    x1, y1 = p1
    x2, y2 = p2

    num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    den = math.hypot(y2 - y1, x2 - x1)
    if den == 0:
        return False
    dist = num / den

    dot = ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1))
    if dot < 0 or dot > (x2 - x1) ** 2 + (y2 - y1) ** 2:
        return False

    return dist <= ball.r

# --- setup balls function ---
def create_balls():
    balls = []
    colors = [(255, 50, 50), (50, 255, 50), (50, 150, 255),
              (255, 255, 50), (255, 50, 255), (50, 255, 255)]
    for i in range(6):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(50, 200)
        x = CENTER[0] + math.cos(angle) * radius
        y = CENTER[1] + math.sin(angle) * radius
        b = Ball(x, y, 20, colors[i], f"B{i+1}")
        bx = CENTER[0] + math.cos(angle) * ARENA_RADIUS
        by = CENTER[1] + math.sin(angle) * ARENA_RADIUS
        b.lines.append((bx, by))
        balls.append(b)
    return balls

# --- fonts ---
font = pygame.font.SysFont(None, 30)
bigfont = pygame.font.SysFont(None, 50)

# --- timer/game vars ---
GAME_TIME = 120

def reset_game():
    global balls, start_time, game_over, winner_text, paused, pause_offset
    balls = create_balls()
    start_time = time.time()
    game_over = False
    winner_text = ""
    paused = False
    pause_offset = 0

reset_game()

# --- main loop ---
running = True
while running:
    screen.fill((10, 10, 10))
    pygame.draw.circle(screen, (200, 200, 200), CENTER, ARENA_RADIUS, 3)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # restart key
                reset_game()
            elif event.key == pygame.K_SPACE:  # pause toggle
                if not paused:
                    paused = True
                    pause_start = time.time()
                else:
                    paused = False
                    pause_offset += time.time() - pause_start

    if not paused:
        elapsed = int(time.time() - start_time - pause_offset)
    else:
        elapsed = int(pause_start - start_time - pause_offset)

    remaining = max(0, GAME_TIME - elapsed)

    alive_balls = [b for b in balls if b.alive]

    # --- WIN CONDITIONS ---
    if not game_over and not paused:
        if len(alive_balls) == 1:
            game_over = True
            for b in balls:
                b.speed = 0
            winner_text = f"{alive_balls[0].name} Wins!"
        elif remaining == 0:
            game_over = True
            for b in balls:
                b.speed = 0
            scores = [len(b.lines) for b in balls]
            max_score = max(scores)
            leaders = [b for b in balls if len(b.lines) == max_score]
            if len(leaders) == 1:
                winner_text = f"{leaders[0].name} Wins!"
            else:
                winner_text = "Draw!"

    # --- update + draw ---
    if not game_over and not paused:
        for ball in balls:
            ball.move()
            ball.draw()

        for b in balls:
            if b.alive:
                for bp in b.lines:
                    pygame.draw.line(screen, b.color, (b.x, b.y), bp, 2)

        for i, b1 in enumerate(balls):
            for j, b2 in enumerate(balls):
                if i < j:
                    b1.check_collision(b2)

        for i, owner in enumerate(balls):
            for bp in owner.lines[:]:
                for k, challenger in enumerate(balls):
                    if k != i and challenger.alive:
                        if line_intersects_circle((owner.x, owner.y), bp, challenger):
                            if bp in owner.lines:
                                owner.lines.remove(bp)
                                challenger.lines.append(bp)

        for b in balls:
            if b.alive and len(b.lines) == 0:
                b.alive = False

    elif paused:  # game paused
        text = bigfont.render("Paused", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - 70, HEIGHT // 2))

    else:  # game over, show winner
        text = bigfont.render(winner_text, True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - 100, HEIGHT // 2))
        tip = font.render("Press R to Restart", True, (200, 200, 200))
        screen.blit(tip, (WIDTH // 2 - 100, HEIGHT // 2 + 40))

    # --- SCOREBOARD ---
    y_offset = 10
    for b in balls:
        label = f"{b.name}: {len(b.lines)}"
        txt = font.render(label, True, b.color)
        screen.blit(txt, (10, y_offset))
        y_offset += 25

    # --- TIMER ---
    timer_text = font.render(f"Time Left: {remaining}s", True, (255, 255, 255))
    screen.blit(timer_text, (WIDTH - 200, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

