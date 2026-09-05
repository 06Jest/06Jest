import json
import os
import urllib.request


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]


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

    return data["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]


def main():
    calendar = fetch_contributions()

    days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]

    active_days = sum(
        1
        for day in days
        if day["contributionCount"] > 0
    )

    print(f"Username: {GITHUB_USERNAME}")
    print(f"Total contributions: {calendar['totalContributions']}")
    print(f"Active days: {active_days}")
    print(f"Days returned: {len(days)}")


if __name__ == "__main__":
    main()
