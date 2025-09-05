# q3_recursive_polygon_inset.py
# Draws a recursive inward-indentation pattern on each edge of a regular polygon.
# Prompts the user for: number of sides, side length, recursion depth.

import math
import turtle as T

# ----------------------------
# Core recursive edge function
# ----------------------------
def koch_inset(length: float, depth: int) -> None:
    """
    Draw one edge with an inward-pointing Koch-style indentation.
    For depth=0, just draw a straight segment of 'length'.
    For depth>0, subdivide into 4 segments with turns: -60, +120, -60 (relative).
    """
    if depth == 0:
        T.forward(length)
        return

    L = length / 3.0
    koch_inset(L, depth - 1)
    T.right(60)      # inward turn (toward interior for CCW polygon)
    koch_inset(L, depth - 1)
    T.left(120)
    koch_inset(L, depth - 1)
    T.right(60)
    koch_inset(L, depth - 1)

# ----------------------------
# Polygon drawing
# ----------------------------
def draw_polygon_inset(n_sides: int, side_len: float, depth: int) -> None:
    """
    Draw a regular n-sided polygon counterclockwise.
    Replace each straight edge with the inward Koch-indented edge at 'depth'.
    """
    # Exterior turn per side for a regular polygon (CCW traversal)
    exterior_turn = 360.0 / n_sides

    # A rough centering: compute circumradius (for a regular polygon)
    # and place the turtle so the figure sits mostly centered on screen.
    # Circumradius of the base polygon (depth=0):
    #   R = s / (2*sin(pi/n))
    # Fractal edges lengthen by (4/3)^depth; use this to expand the "radius" a bit.
    if n_sides >= 3:
        base_R = side_len / (2.0 * math.sin(math.pi / n_sides))
    else:
        base_R = side_len

    scale = (4.0 / 3.0) ** depth
    est_R = base_R * scale

    T.penup()
    # Start at bottom of the estimated circumcircle
    T.setheading(0)
    T.goto(-side_len / 2.0, -est_R * 0.55)  # slight fudge to center visually
    T.pendown()

    # Orient so the first edge goes roughly left-to-right
    T.setheading(0)

    # Draw each side with the recursive inset
    for _ in range(n_sides):
        koch_inset(side_len, depth)
        T.left(exterior_turn)

# ----------------------------
# Main / I/O
# ----------------------------
def main():
    # Prompt inputs
    try:
        n = int(input("Enter the number of sides (>=3): ").strip())
        s = float(input("Enter the side length in pixels (e.g., 300): ").strip())
        d = int(input("Enter the recursion depth (e.g., 0–4): ").strip())
    except Exception:
        print("Invalid input. Please enter integers for sides/depth and a number for length.")
        return

    if n < 3:
        print("Number of sides must be at least 3.")
        return
    if s <= 0:
        print("Side length must be positive.")
        return
    if d < 0:
        print("Depth must be 0 or greater.")
        return

    # Turtle setup
    T.title("Recursive Inward-Indentation Polygon")
    T.tracer(False)      # fast drawing
    T.hideturtle()
    T.speed(0)
    T.colormode(255)

    # Draw
    draw_polygon_inset(n, s, d)

    T.tracer(True)
    print("Done. Click the window to close.")
    T.exitonclick()

if __name__ == "__main__":
    main()
