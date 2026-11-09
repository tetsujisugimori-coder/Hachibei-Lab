"""Integer, outward-rounded interval certificates. No binary64 transcendental trust.

Inputs are exact rational values. Fixed-point intervals enclose, never replace,
those values. Finite precision can lose a proof, not turn uncertainty into CLEAR.
See NUMERICS.md for the proof, domain and deliberately conservative bounds.
"""
from fractions import Fraction
from functools import lru_cache
from math import factorial

SCALE = 10 ** 60
TERMS = 32


def ceildiv(a, b):
    return -((-a) // b)


class I:
    __slots__ = ('lo', 'hi')

    def __init__(self, lo, hi=None):
        self.lo = lo
        self.hi = lo if hi is None else hi
        if self.lo > self.hi:
            raise ValueError('reversed enclosure')

    @classmethod
    def exact(cls, value):
        q = Fraction(value)
        return cls(q.numerator * SCALE // q.denominator,
                   ceildiv(q.numerator * SCALE, q.denominator))

    def __add__(self, other):
        return I(self.lo + other.lo, self.hi + other.hi)

    def __neg__(self):
        return I(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        products = [a * b for a in (self.lo, self.hi)
                    for b in (other.lo, other.hi)]
        return I(min(products) // SCALE, ceildiv(max(products), SCALE))

    def div(self, positive_integer):
        if positive_integer <= 0:
            raise ValueError('positive divisor required')
        return I(self.lo // positive_integer,
                 ceildiv(self.hi, positive_integer))

    def abs(self):
        if self.lo >= 0:
            return self
        if self.hi <= 0:
            return -self
        return I(0, max(-self.lo, self.hi))


def atan_bounds(inverse, terms=80):
    # Alternating series bounds: exact rational sum +/- first omitted term.
    x = Fraction(1, inverse)
    total = sum(((-1) ** k * x ** (2*k+1) / (2*k+1)
                 for k in range(terms)), Fraction(0))
    remainder = x ** (2*terms+1) / (2*terms+1)
    return total - remainder, total + remainder


a, b = atan_bounds(5)
c, d = atan_bounds(239)
# Machin: pi = 16 atan(1/5) - 4 atan(1/239).
PI = I(I.exact(16*a - 4*d).lo, I.exact(16*b - 4*c).hi)
ZERO, ONE = I(0), I(SCALE)


@lru_cache(maxsize=4096)
def sincos(degrees):
    """Enclose sin/cos of exact rational degrees, including huge absolute angles."""
    reduced = Fraction(degrees) % 360
    quadrant = (reduced + 45) // 90
    residual = reduced - quadrant * 90  # exactly in [-45,45)
    if residual == 0:
        co, si = ONE, ZERO
    else:
        x = (I.exact(residual) * PI).div(180)
        if max(abs(x.lo), abs(x.hi)) > SCALE:
            raise ArithmeticError('Taylor domain violated')
        xx = x * x
        co, si = ONE, x
        ct, st = ONE, x
        for k in range(1, TERMS):
            ct = -(ct * xx).div((2*k-1)*(2*k))
            st = -(st * xx).div((2*k)*(2*k+1))
            co, si = co + ct, si + st
        # Both are Taylor polynomials through degree 63 (zero odd/even
        # coefficients included); |x|<=1, derivative<=1 => remainder<=1/64!.
        err = ceildiv(SCALE, factorial(2*TERMS))
        co, si = I(co.lo-err, co.hi+err), I(si.lo-err, si.hi+err)
    return ((co, si), (-si, co), (-co, -si), (si, -co))[quadrant % 4]


def local_rectangle(part, pivot=(0, 0)):
    # Subtract exact input rationals before rounding. Small features are never
    # added to a huge world coordinate in binary64.
    cx, cy = (Fraction(v)-Fraction(p) for v,p in zip(part['center'], pivot))
    w, h = (Fraction(v)/2 for v in part['size'])
    return tuple(I.exact(v) for v in (cx, cy, w, h))


def pose(moving, fixed, degrees):
    co, si = sincos(degrees)
    mx,my,hw,hh = moving
    fx,fy,fw,fh = fixed
    x,y = mx*co-my*si, mx*si+my*co
    ac, ass = co.abs(), si.abs()
    rx,ry = hw*ac+hh*ass, hw*ass+hh*ac
    # Hull boxes enclose every vertex of the exact rectangles at this angle.
    mb = (x-rx, x+rx, y-ry, y+ry)
    fb = (fx-fw, fx+fw, fy-fh, fy+fh)
    dx,dy = fx-x,fy-y
    comparisons = ((dx.abs(), rx+fw), (dy.abs(), ry+fh),
                   ((dx*co+dy*si).abs(), hw+fw*ac+fh*ass),
                   ((-dx*si+dy*co).abs(), hh+fw*ass+fh*ac))
    # Genuine fixed and rotating rectangle axes; all four guaranteed overlapping
    # projections imply intersection. Equality certifies closed-set contact.
    overlap = all(distance.hi <= extent.lo for distance, extent in comparisons)
    gap = max(0, fb[0].lo-mb[1].hi, mb[0].lo-fb[1].hi,
              fb[2].lo-mb[3].hi, mb[2].lo-fb[3].hi)
    return overlap, gap


def motion_upper(radius_l1, exact_angle_distance):
    return ((I.exact(radius_l1) * I.exact(exact_angle_distance)) * PI).div(180).hi
