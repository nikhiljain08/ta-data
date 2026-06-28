"""Entity-specific TallyPrime export request builders.

Each function produces a complete TDL-embedded XML envelope for one Tally
entity type.  The XML element tags in the response are chosen to match exactly
what the parsers in app/parser/ expect, so those parsers require no changes.

TDL field name notes
--------------------
* Boolean fields use $$YesNo:$Field to guarantee "Yes"/"No" string output
  (TallyPrime internal booleans are not automatically serialised as such).
* Monetary amounts ($OpeningBalance, $Amount) include a "Dr"/"Cr" suffix in
  Tally's native serialisation; app/parser/base.decimal_amount() handles both.
* Dates ($Date) are serialised by TallyPrime as YYYYMMDD strings in XML
  exports — matching the domain model expectation.
* AlterID and date-range filters are combined into a single TDL formula when
  both are requested.
"""

from __future__ import annotations

from app.tally_sdk.builder import TdlField, TdlSubPart, build_export


def company_request() -> str:
    """Export all companies visible in TallyPrime (gateway-level, no company context).

    TallyPrime's Company collection is accessible without SVCURRENTCOMPANY —
    it lists every company in the active data directory.  This is the correct
    replacement for the deprecated "List of Companies" report name.
    """
    return build_export(
        key="CMP",
        tally_type="Company",
        xml_record_tag="COMPANY",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$BooksFrom", "BOOKSBEGINNINGFROM"),
            TdlField("$StartingFrom", "STARTINGFROM"),
            TdlField("$EndingAt", "ENDINGAT"),
            TdlField("$CountryName", "COUNTRYNAME"),
            TdlField("$StateName", "STATENAME"),
            TdlField("$GSTIN", "GSTIN"),
            TdlField("$AlterID", "ALTERID"),
        ],
        # No company context: Company collection is gateway-scoped.
        # No AlterID filter: company list is tiny, always do a full refresh.
    )


def ledger_group_request(*, company: str, alter_id: int = 0) -> str:
    """Export ledger groups (Group masters).

    Parser expects <GROUP> elements — set as xml_record_tag.
    """
    return build_export(
        key="GRP",
        tally_type="Group",
        xml_record_tag="GROUP",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$Parent", "PARENT"),
            TdlField("$$YesNo:$IsDeemedPositive", "ISDEEMEDPOSITIVE"),
            TdlField("$$YesNo:$IsRevenue", "ISREVENUE"),
            TdlField("$$YesNo:$AffectsStock", "AFFECTSSTOCK"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def ledger_request(*, company: str, alter_id: int = 0) -> str:
    """Export ledger masters (party accounts, bank accounts, etc.)."""
    return build_export(
        key="LED",
        tally_type="Ledger",
        xml_record_tag="LEDGER",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$Parent", "PARENT"),
            TdlField("$$YesNo:$IsDeemedPositive", "ISDEEMEDPOSITIVE"),
            TdlField("$OpeningBalance", "OPENINGBALANCE"),
            TdlField("$ClosingBalance", "CLOSINGBALANCE"),
            TdlField("$GSTRegistrationType", "GSTREGISTRATIONTYPE"),
            TdlField("$GSTIN", "GSTIN"),
            TdlField("$IncomeTaxNumber", "INCOMETAXNUMBER"),
            TdlField("$LedgerMobile", "LEDGERMOBILE"),
            TdlField("$LedgerEmail", "LEDGEREMAIL"),
            TdlField("$CountryName", "COUNTRYNAME"),
            TdlField("$LedgerStateName", "LEDGERSTATENAME"),
            TdlField("$PINCode", "PINCODE"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def unit_request(*, company: str, alter_id: int = 0) -> str:
    """Export unit-of-measure masters."""
    return build_export(
        key="UNIT",
        tally_type="Unit",
        xml_record_tag="UNIT",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$GSTUnitName", "GSTUNITNAME"),
            TdlField("$FormalName", "FORMALNAME"),
            TdlField("$$YesNo:$IsSimpleUnit", "ISSIMPLEUNIT"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def stock_group_request(*, company: str, alter_id: int = 0) -> str:
    """Export stock group (item group) masters."""
    return build_export(
        key="SGRP",
        tally_type="StockGroup",
        xml_record_tag="STOCKGROUP",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$Parent", "PARENT"),
            TdlField("$$YesNo:$IsAddable", "ISADDABLE"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def godown_request(*, company: str, alter_id: int = 0) -> str:
    """Export godown (warehouse / storage location) masters."""
    return build_export(
        key="GDN",
        tally_type="Godown",
        xml_record_tag="GODOWN",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$Parent", "PARENT"),
            # HasNoSpace is TallyPrime's internal field; parser expects HASNOSTOCK
            TdlField("$$YesNo:$HasNoSpace", "HASNOSTOCK"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def voucher_type_request(*, company: str, alter_id: int = 0) -> str:
    """Export voucher type masters (Sales, Purchase, Payment, Receipt, etc.)."""
    return build_export(
        key="VTYP",
        tally_type="VoucherType",
        xml_record_tag="VOUCHERTYPE",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$Parent", "PARENT"),
            TdlField("$NumberingMethod", "NUMBERINGMETHOD"),
            TdlField("$$YesNo:$IsActive", "ISACTIVE"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def stock_item_request(*, company: str, alter_id: int = 0) -> str:
    """Export stock item (inventory product) masters."""
    return build_export(
        key="SITM",
        tally_type="StockItem",
        xml_record_tag="STOCKITEM",
        fields=[
            TdlField("$Name", "NAME"),
            TdlField("$GUID", "GUID"),
            TdlField("$Parent", "PARENT"),
            TdlField("$Category", "CATEGORY"),
            TdlField("$BaseUnits", "BASEUNITS"),
            TdlField("$GSTApplicable", "GSTAPPLICABLE"),
            TdlField("$GSTTypeOfSupply", "GSTTYPEOFSUPPLY"),
            TdlField("$HSNCode", "HSNCODE"),
            TdlField("$Description", "DESCRIPTION"),
            TdlField("$OpeningBalance", "OPENINGBALANCE"),
            TdlField("$OpeningRate", "OPENINGRATE"),
            TdlField("$OpeningValue", "OPENINGVALUE"),
            TdlField("$ClosingBalance", "CLOSINGBALANCE"),
            TdlField("$ClosingRate", "CLOSINGRATE"),
            TdlField("$ClosingValue", "CLOSINGVALUE"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
    )


def voucher_request(
    *,
    company: str,
    from_date: str,
    to_date: str,
    alter_id: int = 0,
) -> str:
    """Export vouchers with all ledger entries and inventory entries.

    Sub-parts use TallyPrime's "ChildType : ParentType" collection syntax to
    scope the child collection to the current voucher object in the EXPLODE
    context.  The XML tags (ALLLEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST)
    match what the voucher parser expects.

    GST tax details (GSTTAXDETAILS.LIST) are omitted from the TDL export
    because they nest inside inventory entries — a triple-level EXPLODE that
    is not universally supported across TallyPrime builds.  The parser treats
    an absent GSTTAXDETAILS.LIST as an empty gst_details tuple, which is safe.
    """
    ledger_entries_sub = TdlSubPart(
        collection_type="AllLedgerEntries : Voucher",
        xml_record_tag="ALLLEDGERENTRIES.LIST",
        fields=[
            TdlField("$LedgerName", "LEDGERNAME"),
            TdlField("$$YesNo:$IsDeemedPositive", "ISDEEMEDPOSITIVE"),
            TdlField("$Amount", "AMOUNT"),
        ],
    )
    inventory_entries_sub = TdlSubPart(
        collection_type="AllInventoryEntries : Voucher",
        xml_record_tag="ALLINVENTORYENTRIES.LIST",
        fields=[
            TdlField("$StockItemName", "STOCKITEMNAME"),
            TdlField("$$YesNo:$IsDeemedPositive", "ISDEEMEDPOSITIVE"),
            TdlField("$ActualQty", "ACTUALQTY"),
            TdlField("$Rate", "RATE"),
            TdlField("$Amount", "AMOUNT"),
            TdlField("$GodownName", "GODOWNNAME"),
        ],
    )
    return build_export(
        key="VOC",
        tally_type="Voucher",
        xml_record_tag="VOUCHER",
        fields=[
            TdlField("$VoucherNumber", "VOUCHERNUMBER"),
            TdlField("$VoucherTypeName", "VOUCHERTYPENAME"),
            TdlField("$Date", "DATE"),
            TdlField("$PartyLedgerName", "PARTYLEDGERNAME"),
            TdlField("$Narration", "NARRATION"),
            TdlField("$$YesNo:$IsInvoice", "ISINVOICE"),
            TdlField("$$YesNo:$IsCancelled", "ISCANCELLED"),
            TdlField("$$YesNo:$IsOptional", "ISOPTIONAL"),
            TdlField("$GUID", "GUID"),
            TdlField("$AlterID", "ALTERID"),
        ],
        company=company,
        alter_id=alter_id,
        from_date=from_date,
        to_date=to_date,
        sub_parts=[ledger_entries_sub, inventory_entries_sub],
    )
