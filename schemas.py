from pydantic import BaseModel, Field
from typing import Optional, Literal

class ShipmentExtraction(BaseModel):
    id: str
    product_line: Literal["pl_sea_import_lcl", "pl_sea_export_lcl"]
    incoterm: Literal["FOB", "CIF", "CFR", "EXW", "DDP", "DAP", "FCA", "CPT", "CIP", "DPU"] = "FOB"
    # origin_port_code: Optional[str] = None
    origin_port_name: Optional[str]
    # destination_port_code: Optional[str] = None
    destination_port_name: Optional[str]
    cargo_weight_kg: Optional[float]
    cargo_cbm: Optional[float]
    is_dangerous: bool