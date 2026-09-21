def supplier_dict(s):
    return {
        "id": s.id,
        "name": s.name,
        "contact_name": s.contact_name,
        "phone": s.phone,
        "email": s.email,
        "lead_time_days": s.lead_time_days,
        "rating": float(s.rating),
        "active": s.active,
    }


def product_dict(p):
    return {
        "id": p.id,
        "sku": p.sku,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "supplier": p.supplier.name if p.supplier else None,
        "price": float(p.price),
        "stock_qty": p.stock_qty,
        "reorder_level": p.reorder_level,
        "reorder_qty": p.reorder_qty,
        "stock_status": p.stock_status,
        "bin_location": p.bin_location,
        "barcode": p.barcode,
    }


def quotation_dict(q):
    return {
        "id": q.id,
        "quote_no": q.quote_no,
        "customer_name": q.customer_name,
        "customer_company": q.customer_company,
        "total": float(q.total),
        "status": q.status,
        "valid_until": q.valid_until.isoformat(),
        "created_by": q.created_by.get_full_name() or q.created_by.username if q.created_by else "System",
    }
