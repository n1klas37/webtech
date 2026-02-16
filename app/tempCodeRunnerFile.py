    db.add(models.CategoryField(category_id=cat_fit.id, label="Gewicht", data_type="number", unit="kg"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Energie", data_type="number", unit="kcal"))

    # 2. Ernährung
    cat