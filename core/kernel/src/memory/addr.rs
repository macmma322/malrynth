//! Checked physical address and frame types.

/// Hardware page size used by M1A.
pub const PAGE_SIZE: u64 = 4096;

/// A physical byte address.
#[repr(transparent)]
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct PhysicalAddress(u64);

impl PhysicalAddress {
    /// Constructs an address.
    #[must_use]
    pub const fn new(value: u64) -> Self {
        Self(value)
    }

    /// Returns the raw address.
    #[must_use]
    pub const fn as_u64(self) -> u64 {
        self.0
    }

    /// Adds a byte count without wrapping.
    #[must_use]
    pub const fn checked_add(self, bytes: u64) -> Option<Self> {
        match self.0.checked_add(bytes) {
            Some(value) => Some(Self(value)),
            None => None,
        }
    }

    /// Aligns down to `alignment`, which must be a power of two.
    #[must_use]
    pub const fn align_down(self, alignment: u64) -> Option<Self> {
        if !alignment.is_power_of_two() {
            return None;
        }
        Some(Self(self.0 & !(alignment - 1)))
    }

    /// Aligns up to `alignment` without wrapping.
    #[must_use]
    pub const fn checked_align_up(self, alignment: u64) -> Option<Self> {
        if !alignment.is_power_of_two() {
            return None;
        }
        match self.0.checked_add(alignment - 1) {
            Some(value) => Some(Self(value & !(alignment - 1))),
            None => None,
        }
    }
}

/// A 4 KiB physical frame number.
#[repr(transparent)]
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct PhysicalFrame(u64);

impl PhysicalFrame {
    /// Constructs a frame from its number.
    #[must_use]
    pub const fn from_number(number: u64) -> Self {
        Self(number)
    }

    /// Converts an aligned physical address to a frame.
    #[must_use]
    pub const fn from_address(address: PhysicalAddress) -> Option<Self> {
        if address.as_u64().is_multiple_of(PAGE_SIZE) {
            Some(Self(address.as_u64() / PAGE_SIZE))
        } else {
            None
        }
    }

    /// Returns the frame number.
    #[must_use]
    pub const fn number(self) -> u64 {
        self.0
    }

    /// Returns the frame's base address.
    #[must_use]
    pub const fn start_address(self) -> Option<PhysicalAddress> {
        match self.0.checked_mul(PAGE_SIZE) {
            Some(value) => Some(PhysicalAddress::new(value)),
            None => None,
        }
    }
}

/// A half-open range of physical frames.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FrameRange {
    /// First frame in the range.
    pub start: PhysicalFrame,
    /// Frame one past the range.
    pub end: PhysicalFrame,
}

impl FrameRange {
    /// Constructs a non-inverted half-open range.
    #[must_use]
    pub const fn new(start: PhysicalFrame, end: PhysicalFrame) -> Option<Self> {
        if start.number() <= end.number() {
            Some(Self { start, end })
        } else {
            None
        }
    }

    /// Number of frames in the range.
    #[must_use]
    pub const fn len(self) -> u64 {
        self.end.number() - self.start.number()
    }

    /// Whether the range is empty.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.start.number() == self.end.number()
    }

    /// Whether the range contains a frame.
    #[must_use]
    pub const fn contains(self, frame: PhysicalFrame) -> bool {
        frame.number() >= self.start.number() && frame.number() < self.end.number()
    }

    /// Returns the intersection of two ranges.
    #[must_use]
    pub const fn intersection(self, other: Self) -> Option<Self> {
        let start = if self.start.number() > other.start.number() {
            self.start
        } else {
            other.start
        };
        let end = if self.end.number() < other.end.number() {
            self.end
        } else {
            other.end
        };
        if start.number() < end.number() {
            Some(Self { start, end })
        } else {
            None
        }
    }
}
