import json
import os
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]

OUTPUT_DIR = Path("profile")


QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "username": GITHUB_USERNAME,
        },
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "github-profile-stats",
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        data = json.load(response)

    if "errors" in data:
        raise RuntimeError(
            f"GitHub API error: {data['errors']}"
        )

    user = data.get("data", {}).get("user")

    if not user:
        raise RuntimeError(
            f"GitHub user '{GITHUB_USERNAME}' was not found."
        )

    return user["contributionsCollection"]["contributionCalendar"]


def get_last_365_days(calendar):
    all_days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]

    today = date.today()
    start_date = today - timedelta(days=364)

    days = []

    for day in all_days:
        day_date = date.fromisoformat(day["date"])

        if start_date <= day_date <= today:
            days.append({
                "date": day_date,
                "count": day["contributionCount"],
            })

    days.sort(key=lambda day: day["date"])

    if len(days) != 365:
        raise RuntimeError(
            f"Expected 365 days but received {len(days)}."
        )

    return days


def calculate_active_days(days):
    return sum(
        1
        for day in days
        if day["count"] > 0
    )


def calculate_current_streak(days):
    streak = 0

    for day in reversed(days):
        if day["count"] > 0:
            streak += 1
        else:
            break

    return streak


def calculate_longest_streak(days):
    longest = 0
    current = 0

    for day in days:
        if day["count"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def generate_svg(
    *,
    active_days,
    current_streak,
    longest_streak,
    total_contributions,
    dark,
):
    if dark:
        background = "#17171B"
        foreground = "#F5F2EA"
        secondary = "#AAA6AE"
        border = "#3A383F"
        accent = "#E06447"
    else:
        background = "#FCFAF5"
        foreground = "#17171B"
        secondary = "#5E5B63"
        border = "#D8D2C7"
        accent = "#C54B32"

    today = date.today()
    start_date = today - timedelta(days=364)

    title = escape(
        f"{GITHUB_USERNAME} · ACTIVITY / CONSISTENCY"
    )

    date_range = escape(
        f"{start_date.strftime('%b %d, %Y').upper()} — "
        f"{today.strftime('%b %d, %Y').upper()}"
    )

    return f"""<svg
xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 1000 220"
width="1000"
height="220"
role="img"
aria-label="{title}"
>
<rect width="1000" height="220" fill="{background}"/>
<rect
    x="0.5"
    y="0.5"
    width="999"
    height="219"
    fill="none"
    stroke="{border}"
/>

<text
    x="28"
    y="31"
    fill="{foreground}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="11"
    font-weight="700"
    letter-spacing="0.4"
>{title}</text>

<text
    x="972"
    y="31"
    fill="{secondary}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="9"
    font-weight="600"
    text-anchor="end"
>{date_range}</text>


<!-- Active days -->

<text
    x="28"
    y="105"
    fill="{foreground}"
    font-family="ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"
    font-size="56"
    font-weight="700"
    letter-spacing="-3"
>{active_days}</text>

<text
    x="112"
    y="83"
    fill="{secondary}"
    font-family="ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"
    font-size="18"
    font-weight="650"
>/ 365</text>

<text
    x="112"
    y="105"
    fill="{foreground}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="10"
    font-weight="700"
>ACTIVE DAYS</text>


<!-- Divider -->

<path
    d="M300 61L300 126"
    stroke="{border}"
/>


<!-- Current streak -->

<text
    x="335"
    y="100"
    fill="{accent}"
    font-family="ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"
    font-size="42"
    font-weight="700"
>{current_streak}</text>

<text
    x="335"
    y="121"
    fill="{secondary}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="8"
    font-weight="650"
>CURRENT STREAK · DAYS</text>


<!-- Longest streak -->

<text
    x="565"
    y="100"
    fill="{foreground}"
    font-family="ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"
    font-size="42"
    font-weight="700"
>{longest_streak}</text>

<text
    x="565"
    y="121"
    fill="{secondary}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="8"
    font-weight="650"
>LONGEST STREAK · DAYS</text>


<!-- Contributions -->

<text
    x="28"
    y="169"
    fill="{foreground}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="10"
    font-weight="700"
>{total_contributions} CONTRIBUTIONS · PAST YEAR</text>

<path
    d="M28 184L972 184"
    stroke="{border}"
/>

<text
    x="28"
    y="204"
    fill="{secondary}"
    font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace"
    font-size="8"
    font-weight="650"
>ACTIVE DAYS AND STREAKS · DERIVED FROM DAILY COUNTS</text>

</svg>
"""


def write_cards(
    *,
    active_days,
    current_streak,
    longest_streak,
    total_contributions,
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    light_svg = generate_svg(
        active_days=active_days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_contributions=total_contributions,
        dark=False,
    )

    dark_svg = generate_svg(
        active_days=active_days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_contributions=total_contributions,
        dark=True,
    )

    light_path = (
        OUTPUT_DIR /
        "activity-consistency-wide-light.svg"
    )

    dark_path = (
        OUTPUT_DIR /
        "activity-consistency-wide-dark.svg"
    )

    light_path.write_text(
        light_svg,
        encoding="utf-8",
    )

    dark_path.write_text(
        dark_svg,
        encoding="utf-8",
    )

    print(f"Generated {light_path}")
    print(f"Generated {dark_path}")


def main():
    calendar = fetch_contributions()

    days = get_last_365_days(calendar)

    active_days = calculate_active_days(days)
    current_streak = calculate_current_streak(days)
    longest_streak = calculate_longest_streak(days)

    total_contributions = sum(
        day["count"]
        for day in days
    )

    print(f"Username: {GITHUB_USERNAME}")
    print(f"Total contributions: {total_contributions}")
    print(f"Active days: {active_days}")
    print(f"Current streak: {current_streak}")
    print(f"Longest streak: {longest_streak}")
    print(f"Days used: {len(days)}")

    write_cards(
        active_days=active_days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_contributions=total_contributions,
    )


if __name__ == "__main__":
    main()
