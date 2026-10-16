import json
import os
import urllib.parse
import urllib.request
from django.core.management.base import BaseCommand, CommandError
from catalogue.models import Category, Video, Levels


class Command(BaseCommand):
    help = "Imports educational videos from the YouTube Data API v3 into the Lumina catalogue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--query",
            default="python programming tutorial",
            help="Search phrase, e.g. python tutorial",
        )
        parser.add_argument(
            "--max-results",
            type=int,
            default=10,
            help="Number of videos to fetch (max 50)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            raise CommandError(
                "YOUTUBE_API_KEY environment variable is missing. Set it in your .env file or export it in your terminal."
            )

        query = options["query"]
        limit = max(1, min(options["max_results"], 50))

        params = urllib.parse.urlencode({
            "part": "snippet",
            "q": query,
            "maxResults": limit,
            "type": "video",
            "key": api_key,
        })
        url = f"https://www.googleapis.com/youtube/v3/search?{params}"

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "LuminaELibrary/1.0"},
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise CommandError(
                f"Could not fetch YouTube search results: {exc}"
            )

        # Get or create the category, supplying the required unique slug
        category, _ = Category.objects.get_or_create(
            name="Educational Videos",
            defaults={
                "slug": "educational-videos",
                "description": "Video tutorials and lectures",
            },
        )

        created = 0
        skipped = 0

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            title = (snippet.get("title") or "").strip()
            description = (snippet.get("description") or "").strip()
            
            video_id = item.get("id", {}).get("videoId")
            if not video_id or not title:
                skipped += 1
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail = (
                snippet.get("thumbnails", {}).get("high", {}).get("url")
                or snippet.get("thumbnails", {}).get("default", {}).get("url", "")
            )

            # Avoid duplicates by video_url, including the required level field
            video, obj_created = Video.objects.get_or_create(
                video_url=video_url,
                defaults={
                    "title": title,
                    "description": description,
                    "thumbnail": thumbnail,
                    "category": category,
                    "level": Levels.ALL,
                },
            )

            if obj_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {created} videos. Skipped {skipped} duplicates/invalid items."
            )
        )