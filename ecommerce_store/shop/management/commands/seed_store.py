# 2) store/management/commands/seed_store.py
# create directories: store/management/commands/__init__.py (empty) and this file
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from shop.models import Category, Product
import decimal, io, base64

# small placeholder png (1x1 white) base64 to avoid needing image files — optional
PLACEHOLDER_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
    "ASsJTYQAAAAASUVORK5CYII="
)

class Command(BaseCommand):
    help = "Seed the DB with example categories and products."

    def handle(self, *args, **options):
        # Create categories
        cat, _ = Category.objects.get_or_create(slug="gadgets", defaults={"name":"Gadgets", "description":"Electronic gadgets"})
        cat2, _ = Category.objects.get_or_create(slug="books", defaults={"name":"Books", "description":"Books & stationery"})
        # Example products
        products = [
            {"name":"Smart Speaker Mini","slug":"smart-speaker-mini","price":899.00,"gst_percent":18,"stock":20,"category":cat,"description":"Small voice-enabled smart speaker."},
            {"name":"Wireless Headphones","slug":"wireless-headphones","price":1999.00,"gst_percent":18,"stock":15,"category":cat,"description":"Comfortable Bluetooth headphones."},
            {"name":"Python Programming Book","slug":"python-programming","price":499.00,"gst_percent":5,"stock":50,"category":cat2,"description":"Learn Python with hands-on examples."},
        ]
        for p in products:
            prod, created = Product.objects.get_or_create(slug=p["slug"], defaults={
                "name":p["name"], "description":p["description"], "price":decimal.Decimal(str(p["price"])),
                "gst_percent":decimal.Decimal(str(p["gst_percent"])), "stock":p["stock"], "category":p["category"]
            })
            if created:
                # attach tiny placeholder image so templates show a picture (optional)
                data = base64.b64decode(PLACEHOLDER_BASE64)
                prod.image.save(f"{prod.slug}.png", ContentFile(data), save=True)
                self.stdout.write(self.style.SUCCESS(f"Created product: {prod.name}"))
            else:
                self.stdout.write(f"Exists: {prod.name}")
        self.stdout.write(self.style.SUCCESS("Seeding finished."))
