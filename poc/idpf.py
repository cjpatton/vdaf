"""Definition of IDPFs."""

from abc import ABCMeta, abstractmethod
from typing import Generic, Sequence, TypeAlias, TypeVar, Union

from field import Field

FieldInner = TypeVar("FieldInner", bound=Field)
FieldLeaf = TypeVar("FieldLeaf", bound=Field)

# Type alias for the output of `eval()`.
Output: TypeAlias = Union[list[list[FieldInner]], list[list[FieldLeaf]]]
# Type alias for a vector over the inner or leaf field.
FieldVec: TypeAlias = Union[list[FieldInner], list[FieldLeaf]]


class Idpf(Generic[FieldInner, FieldLeaf], metaclass=ABCMeta):
    """
    An Incremental Distributed Point Function (IDPF).

    Generic type parameters:
    FieldInner -- The finite field used to represent the inner nodes of the
        IDPF tree.
    FieldLeaf -- The finite field used to represent the leaf nodes of the IDPF
        tree.

    Attributes:
    SHARES -- Number of keys generated by the IDPF-key generation algorithm.
    BITS -- Bit length of valid input values (i.e., the length of `alpha` in
        bits).
    VALUE_LEN -- The length of each output vector (i.e., the length of
        `beta_leaf` and each element of `beta_inner`).
    KEY_SIZE -- Size in bytes of each IDPF key share.
    RAND_SIZE -- Number of random bytes consumed by the `gen()` algorithm.
    field_inner -- Class object for the field used in inner nodes.
    field_leaf -- Class object for the field used in leaf nodes.
    """

    # Number of keys generated by the IDPF-key generation algorithm.
    SHARES: int

    # Bit length of valid input values (i.e., the length of `alpha` in bits).
    BITS: int

    # The length of each output vector (i.e., the length of `beta_leaf` and
    # each element of `beta_inner`).
    VALUE_LEN: int

    # Size in bytes of each IDPF key share.
    KEY_SIZE: int

    # Number of random bytes consumed by the `gen()` algorithm.
    RAND_SIZE: int

    # Class object for the field used in inner nodes.
    field_inner: type[FieldInner]

    # Class object for the field used in leaf nodes.
    field_leaf: type[FieldLeaf]

    # Name of the IDPF, for use in test vector filenames.
    test_vec_name: str

    @abstractmethod
    def gen(self,
            alpha: int,
            beta_inner: list[list[FieldInner]],
            beta_leaf: list[FieldLeaf],
            binder: bytes,
            rand: bytes) -> tuple[bytes, list[bytes]]:
        """
        Generates an IDPF public share and sequence of IDPF-keys of length
        `SHARES`. Input `alpha` is the index to encode. Inputs `beta_inner` and
        `beta_leaf` are assigned to the values of the nodes on the non-zero
        path of the IDPF tree. String `binder` is a binder string.

        Pre-conditions:

            - `alpha` in `range(2 ** self.BITS)`
            - `len(beta_inner) == self.BITS - 1`
            - `len(beta_inner[level]) == self.VALUE_LEN` for each `level` in
              `range(self.BITS - 1)`
            - `len(beta_leaf) == self.VALUE_LEN`
            - `len(rand) == self.RAND_SIZE`
        """
        pass

    @abstractmethod
    def eval(self,
             agg_id: int,
             public_share: bytes,
             key: bytes,
             level: int,
             prefixes: Sequence[int],
             binder: bytes) -> Output[FieldInner, FieldLeaf]:
        """
        Evaluate an IDPF key share public share at a given level of the tree
        and with the given sequence of prefixes. The output is a vector where
        each element is a vector of length `VALUE_LEN`. The output field is
        `FieldLeaf` if `level == BITS` and `FieldInner` otherwise. `binder`
        must match the binder string passed by the Client to `gen`.

        Let `LSB(x, L)` denote the least significant `L` bits of positive
        integer `x`. By definition, a positive integer `x` is said to be the
        length-`L` prefix of positive integer `y` if `LSB(x, L)` is equal to
        the most significant `L` bits of `LSB(y, BITS)`, For example, 6 (110 in
        binary) is the length-3 prefix of 25 (11001), but 7 (111) is not.

        Each element of `prefixes` is an integer in `[0, 2^level)`. For each
        element of `prefixes` that is the length-`level` prefix of the input
        encoded by the IDPF-key generation algorithm (i.e., `alpha`), the sum
        of the corresponding output shares will be equal to one of the
        programmed output vectors (i.e., an element of `beta_inner +
        [beta_leaf]`). For all other elements of `prefixes`, the corresponding
        output shares will sum up to the 0-vector.

        Pre-conditions:

            - `agg_id` in `range(self.SHARES)`
            - `level` in `range(self.BITS)`
            - `prefix` in `range(2 ** level)` for each `prefix` in `prefixes`
        """
        pass

    def current_field(self, level: int) -> Union[type[FieldInner], type[FieldLeaf]]:
        if level < self.BITS - 1:
            return self.field_inner
        else:
            return self.field_leaf

    def is_prefix(self, x: int, y: int, level: int) -> bool:
        """
        Returns `True` iff `x` is the prefix of `y` at level `level`.

        Pre-conditions:

            - `level` in `range(self.BITS)`
        """
        return y >> (self.BITS - 1 - level) == x
