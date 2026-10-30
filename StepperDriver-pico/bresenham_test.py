from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


LEAD_STEPS = 7
FOLLOW_STEPS = 3
LEAD_PULSE_WIDTH = 0.5
IMAGE_SIZE = (1200, 820)
BACKGROUND = (250, 250, 248)
INK = (38, 45, 54)
GRID = (218, 222, 226)
LEAD_COLOR = (45, 110, 190)
FOLLOW_COLOR = (224, 112, 55)


def pulse_times(
    lead: int, follow: int
) -> tuple[list[float], list[float], list[float], float]:
    if lead <= 0 or follow < 0 or follow > lead:
        raise ValueError("Expected lead > 0 and 0 <= follow <= lead")

    duration = float(lead)
    lead_rises = [float(step) for step in range(lead)]
    follow_rises = [step * duration / follow for step in range(follow)] if follow else []
    follow_pulse_widths = [
        ((follow_rises[index + 1] if index + 1 < follow else duration) - rise) / 2
        for index, rise in enumerate(follow_rises)
    ]
    return lead_rises, follow_rises, follow_pulse_widths, duration


def draw_waveform(
    draw: ImageDraw.ImageDraw,
    rises: list[float],
    pulse_widths: list[float],
    x0: int,
    y_high: int,
    y_low: int,
    scale: float,
    color: tuple[int, int, int],
    duration: float,
) -> None:
    previous_x = x0
    for rise, pulse_width in zip(rises, pulse_widths):
        x_rise = x0 + round(rise * scale)
        x_fall = x0 + round((rise + pulse_width) * scale)
        draw.line((previous_x, y_low, x_rise, y_low), fill=color, width=3)
        draw.line((x_rise, y_low, x_rise, y_high), fill=color, width=3)
        draw.line((x_rise, y_high, x_fall, y_high), fill=color, width=3)
        draw.line((x_fall, y_high, x_fall, y_low), fill=color, width=3)
        previous_x = x_fall

    draw.line((previous_x, y_low, x0 + round(duration * scale), y_low), fill=color, width=3)


def create_example_image(output_path: Path) -> tuple[list[float], list[float]]:
    lead_rises, follow_rises, follow_pulse_widths, duration = pulse_times(LEAD_STEPS, FOLLOW_STEPS)
    image = Image.new("RGB", IMAGE_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text((80, 35), "Linear Bresenham pulse timing", fill=INK, font=font)
    draw.text(
        (80, 65),
        f"{LEAD_STEPS} lead steps, {FOLLOW_STEPS} follow steps; "
        f"follow high/low each use half of its {duration / FOLLOW_STEPS:g}-interval period",
        fill=INK,
        font=font,
    )

    timeline_x = 250
    timeline_scale = 110
    timeline_end = timeline_x + round(duration * timeline_scale)
    draw.text((80, 145), "Lead STEP", fill=LEAD_COLOR, font=font)
    draw.text((80, 225), "Follow STEP", fill=FOLLOW_COLOR, font=font)

    for tick in range(LEAD_STEPS + 1):
        x = timeline_x + tick * timeline_scale
        draw.line((x, 125, x, 290), fill=GRID, width=1)
        draw.text((x - 3, 295), str(tick), fill=INK, font=font)
    draw.line((timeline_x, 285, timeline_end, 285), fill=INK, width=1)
    draw.text((timeline_end + 15, 280), "lead intervals", fill=INK, font=font)

    draw_waveform(
        draw, lead_rises, [LEAD_PULSE_WIDTH] * len(lead_rises),
        timeline_x, 155, 185, timeline_scale, LEAD_COLOR, duration,
    )
    draw_waveform(
        draw, follow_rises, follow_pulse_widths,
        timeline_x, 235, 265, timeline_scale, FOLLOW_COLOR, duration,
    )

    draw.text((80, 435), "Follow position over lead-step time", fill=INK, font=font)
    grid_x, grid_y = timeline_x, 700
    x_scale = timeline_scale
    y_scale = 55
    for x in range(LEAD_STEPS + 1):
        px = grid_x + x * x_scale
        draw.line((px, grid_y - FOLLOW_STEPS * y_scale, px, grid_y), fill=GRID, width=1)
        draw.text((px - 3, grid_y + 10), str(x), fill=INK, font=font)
    for y in range(FOLLOW_STEPS + 1):
        py = grid_y - y * y_scale
        draw.line((grid_x, py, grid_x + LEAD_STEPS * x_scale, py), fill=GRID, width=1)
        draw.text((grid_x - 22, py - 4), str(y), fill=INK, font=font)

    draw.text((grid_x + LEAD_STEPS * x_scale + 15, grid_y - 8), "lead-step time", fill=LEAD_COLOR, font=font)
    draw.text((grid_x - 10, grid_y - FOLLOW_STEPS * y_scale - 22), "follow steps", fill=FOLLOW_COLOR, font=font)

    follow_position = 0
    previous_point = (grid_x, grid_y)
    for rise in follow_rises:
        event_x = grid_x + round(rise * x_scale)
        draw.line((previous_point[0], previous_point[1], event_x, previous_point[1]), fill=INK, width=4)
        follow_position += 1
        event_y = grid_y - follow_position * y_scale
        draw.line((event_x, previous_point[1], event_x, event_y), fill=INK, width=4)
        draw.ellipse((event_x - 5, event_y - 5, event_x + 5, event_y + 5), fill=INK)
        previous_point = (event_x, event_y)

    plot_end = (grid_x + round(duration * x_scale), previous_point[1])
    draw.line((*previous_point, *plot_end), fill=INK, width=4)

    follow_falls = [rise + width for rise, width in zip(follow_rises, follow_pulse_widths)]
    draw.text((80, 765), f"Follow rises: {[round(t, 2) for t in follow_rises]}", fill=INK, font=font)
    draw.text((80, 785), f"Follow falls: {[round(t, 2) for t in follow_falls]}", fill=INK, font=font)
    image.save(output_path)
    return lead_rises, follow_rises


if __name__ == "__main__":
    output = Path(__file__).resolve().with_name("bresenham_example.png")
    lead_times, follow_times = create_example_image(output)
    print(f"Saved example image: {output}")
    print(f"Lead pulse times: {lead_times}")
    print(f"Follow pulse times: {follow_times}")
