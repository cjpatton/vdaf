"""Definitions of finite fields used in this spec."""

from typing import Self, TypeVar, cast

from sage.all import GF, PolynomialRing
from sage.rings.finite_rings.finite_field_constructor import FiniteFieldFactory

from common import from_le_bytes, to_le_bytes


class Field:
    """The base class for finite fields."""

    # The prime modulus that defines arithmetic in the field.
    MODULUS: int

    # Number of bytes used to encode each field element.
    ENCODED_SIZE: int

    gf: FiniteFieldFactory

    def __init__(self, val: int):
        assert int(val) < self.MODULUS
        self.val = self.gf(val)

    @classmethod
    def zeros(cls, length: int) -> list[Self]:
        vec = [cls(cls.gf.zero()) for _ in range(length)]
        return vec

    @classmethod
    def rand_vec(cls, length: int) -> list[Self]:
        """
        Return a random vector of field elements of length `length`.
        """
        vec = [cls(cls.gf.random_element()) for _ in range(length)]
        return vec

    # NOTE: The encode_vec() and decode_vec() methods are excerpted in
    # the document, de-indented, as the figure {{field-derived-methods}}.
    # Their width should be limited to 69 columns after de-indenting, or
    # 73 columns before de-indenting, to avoid warnings from xml2rfc.
    # ===================================================================
    @classmethod
    def encode_vec(cls, vec: list[Self]) -> bytes:
        """
        Encode a vector of field elements `vec` as a byte string.
        """
        encoded = bytes()
        for x in vec:
            encoded += to_le_bytes(x.as_unsigned(), cls.ENCODED_SIZE)
        return encoded

    @classmethod
    def decode_vec(cls, encoded: bytes) -> list[Self]:
        """
        Parse a vector of field elements from `encoded`.
        """
        L = cls.ENCODED_SIZE
        if len(encoded) % L != 0:
            raise ValueError(
                'input length must be a multiple of the size of an '
                'encoded field element')

        vec = []
        for i in range(0, len(encoded), L):
            encoded_x = encoded[i:i+L]
            x = from_le_bytes(encoded_x)
            if x >= cls.MODULUS:
                raise ValueError('modulus overflow')
            vec.append(cls(x))
        return vec

    # NOTE: The encode_into_bit_vector() and decode_from_bit_vector()
    # methods are excerpted in the document, de-indented, as the figure
    # {{field-bit-rep}}. Their width should be limited to 69 columns
    # after de-indenting, or 73 columns before de-indenting, to avoid
    # warnings from xml2rfc.
    # ===================================================================
    @classmethod
    def encode_into_bit_vector(
            cls,
            val: int,
            bits: int) -> list[Self]:
        """
        Encode the bit representation of `val` with at most `bits` number
        of bits, as a vector of field elements.

        Pre-conditions:

            - `val >= 0`
            - `bits >= 0`
        """
        if val >= 2 ** bits:
            # Sanity check we are able to represent `val` with `bits`
            # number of bits.
            raise ValueError("Number of bits is not enough to represent "
                             "the input integer.")
        encoded = []
        for l in range(bits):
            encoded.append(cls((val >> l) & 1))
        return encoded

    @classmethod
    def decode_from_bit_vector(cls, vec: list[Self]) -> Self:
        """
        Decode the field element from the bit representation, expressed
        as a vector of field elements `vec`.
        """
        bits = len(vec)
        if cls.MODULUS >> bits == 0:
            raise ValueError("Number of bits is too large to be "
                             "represented by field modulus.")
        decoded = cls(0)
        for (l, bit) in enumerate(vec):
            decoded += cls(1 << l) * bit
        return decoded

    def __add__(self, other: Self) -> Self:
        return self.__class__(self.val + other.val)

    def __neg__(self) -> Self:
        return self.__class__(-self.val)

    def __mul__(self, other: Self) -> Self:
        return self.__class__(self.val * other.val)

    def inv(self) -> Self:
        return self.__class__(self.val**-1)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Field):
            return NotImplemented
        return cast(bool, self.val == other.val)

    def __sub__(self, other: Self) -> Self:
        return self + (-other)

    def __div__(self, other: Self) -> Self:
        return self * other.inv()

    def __pow__(self, n: int) -> Self:
        return self.__class__(self.val ** n)

    def __str__(self) -> str:
        return str(self.val)

    def __repr__(self) -> str:
        return str(self.val)

    def as_unsigned(self) -> int:
        return int(self.gf(self.val))


class FftField(Field):
    # Order of the multiplicative group generated by `Field.gen()`.
    GEN_ORDER: int

    @classmethod
    def gen(cls) -> Self:
        raise NotImplementedError()


class Field2(Field):
    """The finite field GF(2)."""

    MODULUS = 2
    ENCODED_SIZE = 1

    # Sage finite field object.
    gf = GF(MODULUS)

    def conditional_select(self, inp: bytes) -> bytes:
        """
        Return `inp` unmodified if `self == 1`; otherwise return the all-zero
        string of the same length.

        Implementation note: To protect the code from timing side channels, it
        is important to implement this algorithm in constant time.
        """

        # Convert the element into a bitmask such that `m == 255` if
        # `self == 1` and `m == 0` otherwise.
        m = 0
        v = self.as_unsigned()
        for i in range(8):
            m |= v << i
        return bytes(map(lambda x: m & x, inp))


class Field64(FftField):
    """The finite field GF(2^32 * 4294967295 + 1)."""

    MODULUS = 2**32 * 4294967295 + 1
    GEN_ORDER = 2**32
    ENCODED_SIZE = 8

    # Sage finite field object.
    gf = GF(MODULUS)

    @classmethod
    def gen(cls) -> Self:
        return cls(7)**4294967295


class Field96(FftField):
    """The finite field GF(2^64 * 4294966555 + 1)."""

    MODULUS = 2**64 * 4294966555 + 1
    GEN_ORDER = 2**64
    ENCODED_SIZE = 12

    # Sage finite field object.
    gf = GF(MODULUS)

    @classmethod
    def gen(cls) -> Self:
        return cls(3)**4294966555


class Field128(FftField):
    """The finite field GF(2^66 * 4611686018427387897 + 1)."""

    MODULUS = 2**66 * 4611686018427387897 + 1
    GEN_ORDER = 2**66
    ENCODED_SIZE = 16

    # Sage finite field object.
    gf = GF(MODULUS)

    @classmethod
    def gen(cls) -> Self:
        return cls(7)**4611686018427387897


class Field255(Field):
    """The finite field GF(2^255 - 19)."""

    MODULUS = 2**255 - 19
    ENCODED_SIZE = 32

    # Sage finite field object.
    gf = GF(MODULUS)


##
# POLYNOMIAL ARITHMETIC
#

F = TypeVar("F", bound=Field)


def poly_strip(field: type[F], p: list[F]) -> list[F]:
    """Remove leading zeros from the input polynomial."""
    for i in reversed(range(len(p))):
        if p[i] != field(0):
            return p[:i+1]
    return []


def poly_mul(field: type[F], p: list[F], q: list[F]) -> list[F]:
    """Multiply two polynomials."""
    r = [field(0) for _ in range(len(p) + len(q))]
    for i, p_i in enumerate(p):
        for j, q_j in enumerate(q):
            r[i + j] += p_i * q_j
    return poly_strip(field, r)


def poly_eval(field: type[F], p: list[F], eval_at: F) -> F:
    """Evaluate a polynomial at a point."""
    if len(p) == 0:
        return field(0)

    p = poly_strip(field, p)
    result = p[-1]
    for c in reversed(p[:-1]):
        result *= eval_at
        result += c

    return result


def poly_interp(field: type[F], xs: list[F], ys: list[F]) -> list[F]:
    """Compute the Lagrange interpolation polynomial for the given points."""
    R = PolynomialRing(field.gf, 'x')
    p = R.lagrange_polynomial([(x.val, y.val) for (x, y) in zip(xs, ys)])
    return poly_strip(field, list(map(field, p.coefficients())))
