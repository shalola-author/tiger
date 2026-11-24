use crate::block::Block;
use crate::db::{Db, DbKind};
use crate::everything::Everything;
use crate::item::{Item, ItemLoader};
use crate::token::Token;
use crate::validator::Validator;

#[derive(Clone, Debug)]
pub struct TradeGoodType {}

inventory::submit! {
    ItemLoader::Normal(Item::TradeGoodType, TradeGoodType::add)
}

impl TradeGoodType {
    pub fn add(db: &mut Db, key: Token, block: Block) {
        db.add(Item::TradeGoodType, key, block, Box::new(Self {}));
    }
}

impl DbKind for TradeGoodType {
    fn validate(&self, _key: &Token, block: &Block, data: &Everything) {
        let mut vd = Validator::new(block, data);

        vd.field_numeric("base_price");
        vd.field_bool("is_basic");
        vd.field_item("origin", Item::File);
    }
}

#[derive(Clone, Debug)]
pub struct TradeGoodCategory {}

inventory::submit! {
    ItemLoader::Normal(Item::TradeGoodCategory, TradeGoodCategory::add)
}

impl TradeGoodCategory {
    pub fn add(db: &mut Db, key: Token, block: Block) {
        db.add(Item::TradeGoodCategory, key, block, Box::new(Self {}));
    }
}

impl DbKind for TradeGoodCategory {
    fn validate(&self, _key: &Token, block: &Block, data: &Everything) {
        let mut vd = Validator::new(block, data);

        vd.field_list_items("trade_goods", Item::TradeGoodType);
    }
}