#!/usr/bin/env python3
"""
Flashcard/Review System - Spaced repetition for learning

Uses SM-2 algorithm for optimal review scheduling.

Usage:
    python review.py --today              # Show cards due for review
    python review.py --add "Q" "A"        # Add a new card
    python review.py --add "Q" "A" -c dev # Add card with category
    python review.py --list               # Show all cards
    python review.py --stats              # Show review statistics
    python review.py --quiz               # Interactive quiz mode
    python review.py --random             # Random card (for startup)
    python review.py --random-from-files "*.py"  # Random from recent files
    python review.py --export             # Export cards to markdown
    python review.py --import-from FILE   # Import cards from markdown

Categories: dev, concept, tool, workflow, debug, general (customize as needed)
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Data file location
DATA_DIR = Path(__file__).parent.parent / "cursor-data"
FLASHCARDS_FILE = DATA_DIR / "flashcards.json"

# Categories for organizing cards (customize for your domain)
CATEGORIES = ["dev", "concept", "tool", "workflow", "debug", "general"]

# SM-2 Algorithm defaults
DEFAULT_EASE = 2.5
MIN_EASE = 1.3


def load_cards() -> dict:
    """Load flashcards from JSON file."""
    if not FLASHCARDS_FILE.exists():
        return {"cards": [], "stats": {"total_reviews": 0, "streak_days": 0, "last_review_date": None}}
    
    with open(FLASHCARDS_FILE, "r") as f:
        return json.load(f)


def save_cards(data: dict):
    """Save flashcards to JSON file."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(FLASHCARDS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def generate_id() -> str:
    """Generate a unique card ID."""
    return datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))


def add_card(question: str, answer: str, category: str = "general", tags: list = None, source: str = None) -> dict:
    """Add a new flashcard."""
    data = load_cards()
    
    card = {
        "id": generate_id(),
        "question": question,
        "answer": answer,
        "category": category,
        "tags": tags or [],
        "source": source,  # File path or URL this card relates to
        "created": datetime.now().isoformat(),
        "last_review": None,
        "next_review": datetime.now().isoformat(),  # Due immediately
        "ease_factor": DEFAULT_EASE,
        "interval": 0,  # Days until next review
        "repetitions": 0,
        "total_reviews": 0
    }
    
    data["cards"].append(card)
    save_cards(data)
    return card


def get_due_cards(limit: int = None) -> list:
    """Get cards due for review."""
    data = load_cards()
    now = datetime.now()
    
    due = []
    for card in data["cards"]:
        next_review = datetime.fromisoformat(card["next_review"])
        if next_review <= now:
            due.append(card)
    
    # Sort by next_review (oldest first)
    due.sort(key=lambda c: c["next_review"])
    
    if limit:
        due = due[:limit]
    
    return due


def review_card(card_id: str, quality: int) -> dict:
    """
    Review a card with quality rating (0-5).
    
    Quality scale:
        0 - Complete blackout, wrong response
        1 - Incorrect, but remembered upon seeing answer
        2 - Incorrect, but answer seemed easy to recall
        3 - Correct, but with serious difficulty
        4 - Correct, with some hesitation
        5 - Perfect response, no hesitation
    """
    data = load_cards()
    
    card = None
    for c in data["cards"]:
        if c["id"] == card_id:
            card = c
            break
    
    if not card:
        raise ValueError(f"Card not found: {card_id}")
    
    # SM-2 Algorithm
    if quality < 3:
        # Failed - reset repetitions
        card["repetitions"] = 0
        card["interval"] = 1
    else:
        # Passed
        if card["repetitions"] == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 6
        else:
            card["interval"] = round(card["interval"] * card["ease_factor"])
        
        card["repetitions"] += 1
    
    # Update ease factor
    card["ease_factor"] = max(
        MIN_EASE,
        card["ease_factor"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    )
    
    # Update review timestamps
    card["last_review"] = datetime.now().isoformat()
    card["next_review"] = (datetime.now() + timedelta(days=card["interval"])).isoformat()
    card["total_reviews"] += 1
    
    # Update global stats
    data["stats"]["total_reviews"] += 1
    today = datetime.now().strftime("%Y-%m-%d")
    
    if data["stats"]["last_review_date"] == today:
        pass  # Same day, streak continues
    elif data["stats"]["last_review_date"] == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
        data["stats"]["streak_days"] += 1
    else:
        data["stats"]["streak_days"] = 1
    
    data["stats"]["last_review_date"] = today
    
    save_cards(data)
    return card


def get_random_card(category: str = None, from_files: list = None) -> Optional[dict]:
    """Get a random card, optionally filtered by category or source files."""
    data = load_cards()
    cards = data["cards"]
    
    if not cards:
        return None
    
    if category:
        cards = [c for c in cards if c["category"] == category]
    
    if from_files:
        # Filter cards whose source matches any of the files
        filtered = []
        for card in cards:
            if card.get("source"):
                for f in from_files:
                    if f in card["source"]:
                        filtered.append(card)
                        break
        if filtered:
            cards = filtered
    
    if not cards:
        return None
    
    return random.choice(cards)


def get_stats() -> dict:
    """Get review statistics."""
    data = load_cards()
    cards = data["cards"]
    
    now = datetime.now()
    due_count = sum(1 for c in cards if datetime.fromisoformat(c["next_review"]) <= now)
    
    # Calculate mastery levels
    mastered = sum(1 for c in cards if c["interval"] >= 21)  # 3+ weeks
    learning = sum(1 for c in cards if 0 < c["interval"] < 21)
    new = sum(1 for c in cards if c["interval"] == 0)
    
    # Category breakdown
    by_category = {}
    for cat in CATEGORIES:
        by_category[cat] = sum(1 for c in cards if c["category"] == cat)
    
    return {
        "total_cards": len(cards),
        "due_today": due_count,
        "mastered": mastered,
        "learning": learning,
        "new": new,
        "total_reviews": data["stats"]["total_reviews"],
        "streak_days": data["stats"]["streak_days"],
        "by_category": by_category
    }


def list_cards(category: str = None, show_answers: bool = False) -> list:
    """List all cards, optionally filtered by category."""
    data = load_cards()
    cards = data["cards"]
    
    if category:
        cards = [c for c in cards if c["category"] == category]
    
    return cards


def delete_card(card_id: str) -> bool:
    """Delete a card by ID."""
    data = load_cards()
    original_len = len(data["cards"])
    data["cards"] = [c for c in data["cards"] if c["id"] != card_id]
    
    if len(data["cards"]) < original_len:
        save_cards(data)
        return True
    return False


def export_to_markdown() -> str:
    """Export all cards to markdown format."""
    data = load_cards()
    lines = ["# Flashcard Export", "", f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*", ""]
    
    by_category = {}
    for card in data["cards"]:
        cat = card["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(card)
    
    for cat in CATEGORIES:
        if cat in by_category and by_category[cat]:
            lines.append(f"## {cat.upper()}")
            lines.append("")
            for card in by_category[cat]:
                lines.append(f"### Q: {card['question']}")
                lines.append(f"**A:** {card['answer']}")
                if card.get("tags"):
                    lines.append(f"*Tags: {', '.join(card['tags'])}*")
                if card.get("source"):
                    lines.append(f"*Source: {card['source']}*")
                lines.append("")
    
    return "\n".join(lines)


def import_from_markdown(filepath: str) -> int:
    """Import cards from markdown file. Returns count of imported cards."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = path.read_text()
    lines = content.split("\n")
    
    imported = 0
    current_category = "general"
    current_question = None
    current_answer = None
    current_tags = []
    current_source = None
    
    for line in lines:
        line = line.strip()
        
        # Category header
        if line.startswith("## "):
            cat = line[3:].strip().lower()
            if cat in CATEGORIES:
                current_category = cat
        
        # Question
        elif line.startswith("### Q:") or line.startswith("### Q :"):
            # Save previous card if exists
            if current_question and current_answer:
                add_card(current_question, current_answer, current_category, current_tags, current_source)
                imported += 1
            
            current_question = line.split(":", 1)[1].strip()
            current_answer = None
            current_tags = []
            current_source = None
        
        # Answer
        elif line.startswith("**A:**") or line.startswith("**A :**"):
            current_answer = line.split(":", 1)[1].strip()
        
        # Tags
        elif line.startswith("*Tags:"):
            tags_str = line[6:].rstrip("*").strip()
            current_tags = [t.strip() for t in tags_str.split(",")]
        
        # Source
        elif line.startswith("*Source:"):
            current_source = line[8:].rstrip("*").strip()
    
    # Save last card
    if current_question and current_answer:
        add_card(current_question, current_answer, current_category, current_tags, current_source)
        imported += 1
    
    return imported


def format_card_display(card: dict, show_answer: bool = False, show_id: bool = False) -> str:
    """Format a card for display."""
    lines = []
    
    if show_id:
        lines.append(f"[{card['id']}] ({card['category']})")
    else:
        lines.append(f"({card['category']})")
    
    lines.append(f"Q: {card['question']}")
    
    if show_answer:
        lines.append(f"A: {card['answer']}")
    
    if card.get("tags"):
        lines.append(f"   Tags: {', '.join(card['tags'])}")
    
    # Show review info
    if card["last_review"]:
        last = datetime.fromisoformat(card["last_review"]).strftime("%Y-%m-%d")
        lines.append(f"   Last: {last} | Interval: {card['interval']}d | Ease: {card['ease_factor']:.2f}")
    
    return "\n".join(lines)


def interactive_quiz(cards: list):
    """Run interactive quiz mode."""
    if not cards:
        print("No cards due for review!")
        return
    
    print(f"\n{'='*50}")
    print(f"  QUIZ TIME - {len(cards)} cards to review")
    print(f"{'='*50}\n")
    
    for i, card in enumerate(cards, 1):
        print(f"[{i}/{len(cards)}] ({card['category']})")
        print(f"\nQ: {card['question']}\n")
        
        input("Press Enter to reveal answer...")
        print(f"\nA: {card['answer']}\n")
        
        print("Rate your recall (0-5):")
        print("  0: Complete blackout")
        print("  1: Wrong, but recognized answer")
        print("  2: Wrong, answer seemed familiar")
        print("  3: Correct with difficulty")
        print("  4: Correct with hesitation")
        print("  5: Perfect recall")
        
        while True:
            try:
                quality = int(input("\nRating: "))
                if 0 <= quality <= 5:
                    break
                print("Please enter 0-5")
            except ValueError:
                print("Please enter a number 0-5")
            except KeyboardInterrupt:
                print("\n\nQuiz interrupted.")
                return
        
        updated = review_card(card["id"], quality)
        next_review = datetime.fromisoformat(updated["next_review"]).strftime("%Y-%m-%d")
        print(f"\nNext review: {next_review}")
        print(f"\n{'-'*50}\n")
    
    print("Quiz complete!")
    stats = get_stats()
    print(f"Streak: {stats['streak_days']} days | Total reviews: {stats['total_reviews']}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Flashcard review system with spaced repetition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Categories: dev, concept, tool, workflow, debug, general

Quality ratings for review:
  0: Complete blackout
  1: Wrong, but recognized answer
  2: Wrong, answer seemed familiar
  3: Correct with difficulty
  4: Correct with hesitation
  5: Perfect recall

Examples:
  python review.py --today
  python review.py --add "What is X?" "X is a tool for Y"
  python review.py --add "Question" "Answer" -c dev -t "python,debugging"
  python review.py --quiz
  python review.py --random
        """
    )
    
    # Main actions
    parser.add_argument("--today", action="store_true", help="Show cards due for review")
    parser.add_argument("--add", nargs=2, metavar=("Q", "A"), help="Add a new card")
    parser.add_argument("--list", action="store_true", help="List all cards")
    parser.add_argument("--stats", action="store_true", help="Show review statistics")
    parser.add_argument("--quiz", action="store_true", help="Interactive quiz mode")
    parser.add_argument("--random", action="store_true", help="Show a random card")
    parser.add_argument("--random-from-files", nargs="*", help="Random card from specific files")
    parser.add_argument("--export", action="store_true", help="Export cards to markdown")
    parser.add_argument("--import-from", type=str, help="Import cards from markdown file")
    parser.add_argument("--delete", type=str, metavar="ID", help="Delete a card by ID")
    parser.add_argument("--review", nargs=2, metavar=("ID", "QUALITY"), help="Review a specific card")
    parser.add_argument("--digest", action="store_true", help="Short digest for startup (cards due count)")
    
    # Filters
    parser.add_argument("-c", "--category", choices=CATEGORIES, help="Category for new card or filter")
    parser.add_argument("-t", "--tags", type=str, help="Comma-separated tags for new card")
    parser.add_argument("-s", "--source", type=str, help="Source file/URL for new card")
    parser.add_argument("-n", "--limit", type=int, default=5, help="Limit number of cards shown")
    parser.add_argument("--show-answers", action="store_true", help="Show answers in list")
    parser.add_argument("--show-ids", action="store_true", help="Show card IDs")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Show cards due today
    if args.today:
        due = get_due_cards(args.limit)
        if args.json:
            print(json.dumps(due, indent=2))
        elif due:
            print(f"\n{len(due)} card(s) due for review:\n")
            for card in due:
                print(format_card_display(card, args.show_answers, args.show_ids))
                print()
        else:
            print("No cards due for review today!")
        return
    
    # Add new card
    if args.add:
        question, answer = args.add
        tags = args.tags.split(",") if args.tags else []
        card = add_card(question, answer, args.category or "general", tags, args.source)
        if args.json:
            print(json.dumps(card, indent=2))
        else:
            print(f"Added card [{card['id']}]")
            print(f"  Q: {question}")
            print(f"  A: {answer}")
            if args.category:
                print(f"  Category: {args.category}")
        return
    
    # List all cards
    if args.list:
        cards = list_cards(args.category)
        if args.json:
            print(json.dumps(cards, indent=2))
        elif cards:
            print(f"\n{len(cards)} card(s):\n")
            for card in cards:
                print(format_card_display(card, args.show_answers, args.show_ids))
                print()
        else:
            print("No cards found.")
        return
    
    # Show statistics
    if args.stats:
        stats = get_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"\n{'='*40}")
            print("  FLASHCARD STATISTICS")
            print(f"{'='*40}")
            print(f"  Total cards:    {stats['total_cards']}")
            print(f"  Due today:      {stats['due_today']}")
            print(f"  Mastered:       {stats['mastered']}")
            print(f"  Learning:       {stats['learning']}")
            print(f"  New:            {stats['new']}")
            print(f"{'='*40}")
            print(f"  Total reviews:  {stats['total_reviews']}")
            print(f"  Streak:         {stats['streak_days']} days")
            print(f"{'='*40}")
            print("\n  By Category:")
            for cat, count in stats['by_category'].items():
                if count > 0:
                    print(f"    {cat}: {count}")
            print()
        return
    
    # Interactive quiz
    if args.quiz:
        due = get_due_cards()
        if args.category:
            due = [c for c in due if c["category"] == args.category]
        interactive_quiz(due)
        return
    
    # Random card
    if args.random or args.random_from_files:
        card = get_random_card(args.category, args.random_from_files)
        if args.json:
            print(json.dumps(card, indent=2))
        elif card:
            print(f"\n{card['category'].upper()}")
            print(f"\nQ: {card['question']}\n")
            print("[Press Enter to reveal answer]")
        else:
            print("No cards available.")
        return
    
    # Export
    if args.export:
        md = export_to_markdown()
        print(md)
        return
    
    # Import
    if args.import_from:
        try:
            count = import_from_markdown(args.import_from)
            print(f"Imported {count} cards from {args.import_from}")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Delete card
    if args.delete:
        if delete_card(args.delete):
            print(f"Deleted card {args.delete}")
        else:
            print(f"Card not found: {args.delete}")
        return
    
    # Review specific card
    if args.review:
        card_id, quality = args.review
        try:
            updated = review_card(card_id, int(quality))
            next_review = datetime.fromisoformat(updated["next_review"]).strftime("%Y-%m-%d")
            print(f"Reviewed card {card_id}")
            print(f"  Next review: {next_review}")
            print(f"  Interval: {updated['interval']} days")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Digest mode (for startup integration)
    if args.digest:
        stats = get_stats()
        if args.json:
            print(json.dumps({
                "due": stats["due_today"],
                "streak": stats["streak_days"],
                "total": stats["total_cards"]
            }))
        else:
            print(f"{stats['due_today']} cards due | Streak: {stats['streak_days']} days")
        return
    
    # Default: show stats summary
    stats = get_stats()
    print(f"\nFlashcards: {stats['total_cards']} total, {stats['due_today']} due")
    print(f"   Streak: {stats['streak_days']} days")
    if stats['due_today'] > 0:
        print(f"\n   Run 'python review.py --quiz' to review due cards")


if __name__ == "__main__":
    main()
