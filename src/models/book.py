class Book:
    def __init__(self, title, author, public_domain=True):
        self.title = title
        self.author = author
        self.public_domain = public_domain
        self.available = True
        self.reviews = []

    def add_review(self, review):
        self.reviews.append(review)

    def average_rating(self):
        if not self.reviews:
            return 0
        ratings = [r["rating"] for r in self.reviews]
        return round(sum(ratings) / len(ratings), 2)
