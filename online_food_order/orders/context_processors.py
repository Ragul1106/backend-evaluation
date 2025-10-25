from .utils import cart_totals

def cart_count(request):
    total, count = cart_totals(request.session)
    return {"cart_count": count}
