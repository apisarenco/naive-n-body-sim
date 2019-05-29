import itertools
import math
import pyglet
import pyglet.gl as gl
from random import random
from numba import jit


window = pyglet.window.Window(1400, 800)


def make_circle_fill():
    """ Adds a vertex list of circle polygon to batch and returns it. """
    num_points = 40
    batch = pyglet.graphics.Batch()
    rad = math.pi * 2 / num_points # getting 360 / n in radians
    index = list(itertools.chain.from_iterable( (0, x-1, x)  for x in range(2, num_points+1) ))
    index += [0, 1, num_points] # end of fan
    vertices = [0, 0] # adding center of fan
    for i in range(1, num_points + 1):
        angle = rad * i
        vertices += [math.cos(angle), math.sin(angle)]
    vertices += [1, 0] # adding end of fan
    circle = pyglet.graphics.vertex_list_indexed(num_points+2, index, ('v2f', vertices))
    return circle


@jit(nopython=True, cache=True)
def compute_radius(mass):
    return mass**0.333 * 0.4


# Initialize stuff
circlefill = make_circle_fill()

total_objects = 1000

masses = []
radii = []
px = []
py = []
vx = []
vy = []
deleted = []
for i in range(total_objects):
    mass = random() * 100
    masses.append(mass)
    radii.append(compute_radius(mass))
    px.append(random() * 1400)
    py.append(random() * 800)
    vx.append((random() - 0.5) * 4)
    vy.append((random() - 0.5) * 4)
    deleted.append(0)


def timer(dt):
    global total_objects
    total_objects = turn(total_objects, masses, radii, px, py, vx, vy, deleted)


@jit(nopython=True, cache=True)
def turn(total_objects, masses, radii, px, py, vx, vy, deleted):
    to_clean = set()
    for i in range(total_objects):
        for j in range(i + 1, total_objects):
            # distance on each axis
            dx = px[i] - px[j]
            dy = py[i] - py[j]

            # square distances
            dx2 = dx ** 2
            dy2 = dy ** 2
            r2 = dx2 + dy2
            # Used to translate acceleration value into a vector later on
            normalizer = abs(dx) + abs(dy)

            # check collision
            # Objects that are already collided with something else can't collide again
            if deleted[j] == 0 and dx2 + dy2 < (radii[i] + radii[j]) ** 2:
                # j will be removed, i will gain all of j's mass and momentum
                total_mass = masses[i] + masses[j]
                # new coordinates
                px[i] = (px[i] * masses[i] + px[j] * masses[j]) / total_mass
                py[i] = (py[i] * masses[i] + py[j] * masses[j]) / total_mass
                # new velocity based on momentum
                vx[i] = (vx[i] * masses[i] + vx[j] * masses[j]) / total_mass
                vy[i] = (vy[i] * masses[i] + vy[j] * masses[j]) / total_mass

                radii[i] = compute_radius(total_mass)
                masses[i] = total_mass
                # Cleanup j after all of this is over (until then we need to compute its influence on other objects)
                to_clean.add(j)
                deleted[j] = True
            # No collision? Compute interaction
            else:
                vx[i] -= dx * normalizer / r2 * masses[j] / 1000000.0
                vy[i] -= dy * normalizer / r2 * masses[j] / 1000000.0
                vx[j] += dx * normalizer / r2 * masses[i] / 1000000.0
                vy[j] += dy * normalizer / r2 * masses[i] / 1000000.0

        px[i] += vx[i]
        py[i] += vy[i]

    # Clean up deleted objects after the round completion, in reverse order
    for i in sorted(to_clean)[::-1]:
        masses.pop(i)
        radii.pop(i)
        px.pop(i)
        py.pop(i)
        vx.pop(i)
        vy.pop(i)
        deleted.pop(i)
        total_objects -= 1
    return total_objects


@window.event
def on_draw():
    global total_objects
    #total_objects = turn(total_objects, masses, radii, px, py, vx, vy)
    print(total_objects)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    for i in range(total_objects):
        gl.glPushMatrix()
        gl.glColor3f(1,1,0)
        gl.glTranslatef(px[i], py[i], 0)
        gl.glScalef(radii[i], radii[i], 1)
        circlefill.draw(gl.GL_TRIANGLES)
        gl.glPopMatrix()

# Schedule an update every 1/30th of a second. After each update, on_draw() is called automatically
pyglet.clock.schedule_interval(timer, 1/30.0)
pyglet.app.run()
