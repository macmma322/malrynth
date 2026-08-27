//! Physical-memory ownership foundation.

mod addr;
mod physical;

pub use addr::{FrameRange, PAGE_SIZE, PhysicalAddress, PhysicalFrame};
pub use physical::{
    Accounting, BitmapAllocator, CanonicalRegion, FreeError, MapError, OwnershipKind, RawRegion,
    canonicalize, metadata_frames_required, select_metadata_range,
};
