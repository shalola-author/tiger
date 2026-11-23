use std::path::PathBuf;

use crate::block::Block;
use crate::fileset::{FileEntry, FileHandler};
use crate::helpers::TigerHashSet;
use crate::parse::ParserMemory;
use crate::pdxfile::PdxFile;

/// The title types defined in `common/title_types/`.
///
/// A title type assigns properties common to all titles of the same type. The `landless`
/// property is relevant here: noble and merchant family counties are landless by their
/// title type, so they legitimately have no baronies.
#[derive(Clone, Debug, Default)]
pub struct TitleTypes {
    /// The `prefix` of every title type that has `landless = yes`.
    landless_prefixes: TigerHashSet<&'static str>,
}

impl TitleTypes {
    fn load_item(&mut self, block: &Block) {
        let mut landless = block.get_field_bool("landless").unwrap_or(false);
        if let Some(props) = block.get_field_block("properties") {
            landless |= props.get_field_bool("landless").unwrap_or(false);
        }
        if landless
            && let Some(prefix) = block.get_field_value("prefix")
        {
            self.landless_prefixes.insert(prefix.as_str());
        }
    }

    /// Return true iff a title with this key is landless by its title type.
    ///
    /// Per `_title_types.info`, the type prefix appears in the key surrounded by `_` on each
    /// side (preceded by only a tier prefix for game-start titles), e.g. `c_nf_ampelas` or
    /// `c_merchant_starting_gaon_thessalonika`.
    pub fn is_landless(&self, key: &str) -> bool {
        self.landless_prefixes.iter().any(|prefix| {
            let needle = format!("_{prefix}_");
            key.contains(&needle)
        })
    }
}

impl FileHandler<Block> for TitleTypes {
    fn subpath(&self) -> PathBuf {
        PathBuf::from("common/title_types")
    }

    fn load_file(&self, entry: &FileEntry, parser: &ParserMemory) -> Option<Block> {
        if !entry.filename().to_string_lossy().ends_with(".txt") {
            return None;
        }

        PdxFile::read(entry, parser)
    }

    fn handle_file(&mut self, _entry: &FileEntry, mut block: Block) {
        for (_key, block) in block.drain_definitions_warn() {
            self.load_item(&block);
        }
    }
}