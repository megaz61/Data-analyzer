# app/services/data_analyzer.py
# ============================================================
# DataAnalyzer - Profiling dataframe + rekomendasi chart + PDF stats
# Dengan cleansing datetime + resampling + x-axis tanggal (YYYY-MM-DD)
# + legend/series_name supaya keterangan chart tidak "y" lagi.
# ============================================================

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import re, warnings
import numpy as np
import pandas as pd

# ---------- Utils JSON-safe ----------
def _py(v: Any) -> Any:
    if isinstance(v, (np.floating,)): return float(v)
    if isinstance(v, (np.integer,)):  return int(v)
    if isinstance(v, (np.bool_,)):    return bool(v)
    if isinstance(v, (pd.Timestamp, pd.Timedelta)): return str(v)
    if isinstance(v, dict):  return {str(k): _py(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)): return [_py(x) for x in v]
    return v

DATE_PAT = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2})?)?$"
    r"|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}([ T]\d{1,2}:\d{2}(:\d{2})?)?$"
)

class DataAnalyzer:
    def __init__(self)->None:
        warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

    # ======================================================================
    # PUBLIC: CSV/Excel
    # ======================================================================
    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {
            "shape": (int(df.shape[0]), int(df.shape[1])),
            "columns": [str(c) for c in df.columns],
            "dtypes": {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
            "null_counts": {str(k): int(v) for k, v in df.isnull().sum().to_dict().items()},
            "null_percentages": _py(((df.isnull().sum() / max(1, len(df)) * 100).round(2)).to_dict()) if len(df) else {},
            "summary_stats": {},
            "charts": {},
        }

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = [c for c in df.columns if c not in num_cols]

        if num_cols:
            desc = df[num_cols].describe()
            analysis["summary_stats"] = {str(c): {str(s):_py(v) for s,v in desc[c].items()} for c in desc.columns}

        self._add_hist(df, num_cols, analysis["charts"])
        self._add_bar(df, cat_cols, analysis["charts"])

        if len(num_cols) >= 2:
            sc = self._make_scatter(df, num_cols[0], num_cols[1])
            if sc: analysis["charts"][f"scatter_{num_cols[0]}_vs_{num_cols[1]}"] = sc

        analysis["column_types"]  = self._detect_types(df)
        analysis["data_quality"]  = self._quality(df, num_cols)
        analysis["correlations"]  = self._corr(df, num_cols)
        analysis["time_breakdown"]= self._time_breakdown(df)
        analysis["text_overview"] = self._text_overview(df)
        analysis["intelligent_charts"] = self._smart_charts(df, analysis["column_types"], num_cols)
        return _py(analysis)

    def analyze_excel_workbook(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        xls = pd.ExcelFile(file_path)
        sheets: Dict[str, Any] = {}
        for s in xls.sheet_names:
            try:
                sdf = pd.read_excel(file_path, sheet_name=s)
                sheets[s] = {"data": sdf.to_dict("records")[:50], "analysis": self.analyze_dataframe(sdf)}
            except Exception as e:
                sheets[s] = {"data": [], "analysis": {"error": str(e)}}
        summary = {
            "total_sheets": len(sheets),
            "sheet_names": list(sheets.keys()),
            "total_rows": sum(d.get("analysis",{}).get("shape",[0])[0] for d in sheets.values()),
            "total_columns": sum(d.get("analysis",{}).get("shape",[0,0])[1] for d in sheets.values()),
        }
        return sheets, summary

    # ======================================================================
    # PUBLIC: PDF
    # ======================================================================
    def analyze_pdf(
        self,
        full_text: str,
        page_texts: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        gemini_model: Any = None,
        do_summary: bool = True,
    ) -> Dict[str, Any]:
        stats = self._pdf_statistics(full_text, page_texts)

        pages = metadata.get("pages") if metadata else (len(page_texts) if page_texts else 0)
        pages_with_text = sum(1 for p in page_texts or [] if (p.get("word_count",0) > 0))
        extraction_info = {
            "success_rate": round((pages_with_text / max(1, pages)) * 100, 1) if pages else 0.0,
            "pages_with_text": pages_with_text,
            "total_pages": pages,
            "pages_total": pages,  # alias untuk UI yang berbeda
        }
        meta = metadata or {"type": "pdf", "pages": pages, "file_size_bytes": None, "file_size_mb": None, "extractable": pages_with_text>0}

        ai_summary = "Summary not available"
        if do_summary and gemini_model and full_text:
            snippet = full_text[:3000]
            ai_summary = self._pdf_ai_summary(snippet, gemini_model)

        return {
            **stats,
            "ai_summary": ai_summary,
            "metadata": meta,
            "extraction_info": extraction_info,
            "pages": pages,
            "page_count": pages,
        }

    # ======================================================================
    # HELPERS: charts dasar
    # ======================================================================
    def _add_hist(self, df: pd.DataFrame, cols: List[str], charts: Dict[str, Any])->None:
        for col in cols[:5]:
            s = df[col].dropna()
            if s.empty: continue
            try:
                q75, q25 = np.percentile(s,[75,25]); iqr = q75-q25
                bins = max(min(int(np.ceil((s.max()-s.min())/(2*iqr/(len(s)**(1/3))))) if iqr>0 else 10, 30), 5)
            except Exception:
                bins = 10
            counts, edges = np.histogram(s, bins=bins)
            centers = [(edges[i]+edges[i+1])/2 for i in range(len(edges)-1)]
            data_pts = [{"x":_py(x),"y":_py(y)} for x,y in zip(centers, counts.tolist())]
            charts[str(col)] = {
                "type":"histogram",
                "title": f"Distribusi {col}",
                "bins": _py(edges.tolist()),
                "counts": _py(counts.tolist()),
                "stats":{"mean":_py(s.mean()),"median":_py(s.median()),"std":_py(s.std())},
                "data": data_pts,
                "series_name": "Frekuensi",
                "series": [{"name":"Frekuensi","data": data_pts}],
                "x_label":str(col),"y_label":"Frequency","chart_purpose":"distribution",
            }

    def _add_bar(self, df: pd.DataFrame, cols: List[str], charts: Dict[str, Any])->None:
        for col in cols[:5]:
            vc = df[col].astype(str).value_counts().head(12)
            if vc.empty: continue
            cat = vc.index.astype(str).tolist()
            cnt = _py(vc.tolist())
            pts = [{"x": c, "y": v} for c, v in zip(cat, cnt)]
            charts[str(col)] = {
                "type":"bar",
                "title": f"Distribusi {col}",
                "categories": cat,
                "counts": cnt,
                "total_unique": int(df[col].nunique()),
                "top_category_percentage": _py(round((vc.iloc[0]/max(1,len(df)))*100,2)),
                "data": pts,
                "series_name": "Jumlah",
                "series": [{"name":"Jumlah","data": pts}],
                "x_label":str(col),"y_label":"Count","chart_purpose":"distribution",
            }

    # ======================================================================
    # HELPERS: tipe/quality/corr/waktu/teks
    # ======================================================================
    def _detect_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        info: Dict[str, Any] = {}
        for c in df.columns:
            col = df[c].dropna()
            if col.empty:
                info[str(c)] = {"detected_type":"empty","pandas_dtype":str(df[c].dtype),"null_percentage":100.0,"unique_count":0,"sample_values":[]}
                continue
            null_pct = float((df[c].isnull().sum()/max(1,len(df)))*100)
            num = pd.to_numeric(col, errors="coerce")
            if num.notna().mean() >= 0.8:
                is_int = (num.dropna()%1==0).mean() >= 0.95
                info[str(c)] = {"detected_type":"integer" if is_int else "float","pandas_dtype":str(df[c].dtype),
                                "null_percentage":round(null_pct,2),"unique_count":int(col.nunique()),
                                "sample_values":_py(col.head(5).tolist()),
                                "additional_info":{"min":_py(num.min()),"max":_py(num.max()),"mean":_py(num.mean())}}
                continue
            dt = self._maybe_datetime(col)
            if dt is not None:
                info[str(c)] = {"detected_type":"datetime","pandas_dtype":str(df[c].dtype),
                                "null_percentage":round(null_pct,2),"unique_count":int(col.nunique()),
                                "sample_values":_py(col.astype(str).head(5).tolist()),
                                "additional_info":{"earliest":str(dt.min()),"latest":str(dt.max())}}
                continue
            uniq = set(col.astype(str).str.strip().str.lower().unique())
            for tset in [{"true","false"},{"yes","no"},{"y","n"},{"1","0"},{"on","off"}]:
                if uniq.issubset(tset):
                    info[str(c)] = {"detected_type":"boolean","pandas_dtype":str(df[c].dtype),
                                    "null_percentage":round(null_pct,2),"unique_count":int(len(uniq)),
                                    "sample_values":_py(list(uniq))}
                    break
            else:
                u = col.nunique()
                if u <= 20 and (u/len(col)) < 0.5:
                    info[str(c)] = {"detected_type":"categorical","pandas_dtype":str(df[c].dtype),
                                    "null_percentage":round(null_pct,2),"unique_count":int(u),
                                    "sample_values":_py(col.astype(str).head(5).tolist()),
                                    "additional_info":{"top":_py(col.astype(str).value_counts().head(10).to_dict())}}
                else:
                    info[str(c)] = {"detected_type":"text","pandas_dtype":str(df[c].dtype),
                                    "null_percentage":round(null_pct,2),"unique_count":int(u),
                                    "sample_values":_py(col.astype(str).head(5).tolist())}
        return info

    def _maybe_datetime(self, s: pd.Series) -> Optional[pd.Series]:
        s = s.dropna().astype(str).str.strip()
        if s.empty or s.str.match(DATE_PAT).mean() < 0.6: return None
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Could not infer format")
            dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True, utc=True)
        try:
            dt = dt.tz_convert(None)
        except Exception:
            try:
                dt = dt.tz_localize(None)
            except Exception:
                pass
        return dt.dropna() if dt.notna().mean() >= 0.6 else None

    def _quality(self, df: pd.DataFrame, num_cols: List[str]) -> Dict[str, Any]:
        total = int(df.size); nulls = int(df.isnull().sum().sum()); dups = int(df.duplicated().sum())
        high_null = [{"column":str(c),"null_percentage":round(df[c].isnull().mean()*100,2)}
                     for c in df.columns if df[c].isnull().mean()>0.5]
        outliers: Dict[str, Any] = {}
        for c in num_cols[:6]:
            s = df[c].dropna()
            if len(s) < 8: continue
            q1,q3 = np.percentile(s,[25,75]); iqr = q3-q1
            outliers[str(c)] = {"iqr_count": int(((s < (q1-1.5*iqr)) | (s > (q3+1.5*iqr))).sum()),
                                "zscore_gt3": int((((s-s.mean())/(s.std()+1e-9)).abs()>3).sum())}
        score = round(max(0,40*(1-(nulls/total if total else 0))) + max(0,30*(1-(dups/max(1,len(df))))) + 30, 2)
        return {"completeness_percentage":round((1-(nulls/total if total else 0))*100,2),
                "duplicate_rows":dups,"duplicate_percentage":round((dups/max(1,len(df)))*100,2),
                "high_null_columns":high_null,"outliers":outliers,"data_quality_score":score}

    def _corr(self, df: pd.DataFrame, num_cols: List[str]) -> Dict[str, Any]:
        if len(num_cols) < 2: return {"matrix": {}, "strong_pairs": []}
        corr = df[num_cols].corr().fillna(0)
        pairs = []
        for i,c1 in enumerate(num_cols):
            for c2 in num_cols[i+1:]:
                val = float(corr.loc[c1,c2])
                if abs(val) >= 0.6: pairs.append({"pair":[str(c1),str(c2)],"corr":round(val,3)})
        return {"matrix": _py(corr.round(3).to_dict()), "strong_pairs": pairs[:10]}

    def _time_breakdown(self, df: pd.DataFrame) -> Dict[str, Any]:
        cand = []
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]) or self._maybe_datetime(df[c]) is not None:
                cand.append(c)
        if not cand: return {}
        col = cand[0]
        s = pd.to_datetime(df[col], errors="coerce")
        out = {"datetime_column": str(col)}
        try:
            out["by_year"]    = _py(s.dt.year.value_counts().sort_index().to_dict())
            out["by_month"]   = _py(s.dt.month.value_counts().sort_index().to_dict())
            out["by_weekday"] = _py(s.dt.weekday.value_counts().sort_index().to_dict())
        except Exception: pass
        return out

    def _text_overview(self, df: pd.DataFrame, limit: int = 3) -> Dict[str, Any]:
        token_re = re.compile(r"[A-Za-z0-9_]{3,}")
        out: Dict[str, Any] = {}
        text_cols = []
        for c in df.columns:
            if pd.api.types.is_object_dtype(df[c]):
                s = df[c].dropna().astype(str)
                if s.empty: continue
                if (s.nunique()/len(s) > 0.7) and (s.str.len().mean() > 8): text_cols.append(c)
        for c in text_cols[:limit]:
            s = df[c].dropna().astype(str).str.lower()
            bag: Dict[str,int] = {}
            for line in s.head(2000):
                for t in token_re.findall(line):
                    bag[t] = bag.get(t,0)+1
            top = sorted(bag.items(), key=lambda x:-x[1])[:20]
            out[str(c)] = {"top_tokens":[{"token":k,"count":v} for k,v in top]}
        return out

    # ======================================================================
    # TIME-SERIES CLEANING HELPERS
    # ======================================================================
    def _parse_datetime(self, s: pd.Series) -> pd.Series:
        s = s.dropna().astype(str).str.strip()
        if s.empty:
            return pd.to_datetime([], errors="coerce")
        # Heuristik dayfirst
        sample = s.head(60)
        dayfirst_hits = 0
        for x in sample:
            m = re.match(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", x)
            if m:
                first = int(m.group(1)); second = int(m.group(2))
                if first > 12 and second <= 12:
                    dayfirst_hits += 1
        dayfirst = dayfirst_hits >= max(1, len(sample) * 0.2)

        dt = pd.to_datetime(
            s, errors="coerce", infer_datetime_format=True, utc=True, dayfirst=dayfirst
        )
        try:
            dt = dt.tz_convert(None)
        except Exception:
            try:
                dt = dt.tz_localize(None)
            except Exception:
                pass
        return dt.dropna()

    def _prepare_time_series(
        self, df: pd.DataFrame, date_col: str, value_col: str,
        max_points: int = 300
    ) -> Optional[pd.DataFrame]:
        dt = self._parse_datetime(df[date_col])
        vals = pd.to_numeric(df[value_col], errors="coerce")

        ts = pd.DataFrame({"dt": dt, "val": vals}).dropna()
        if ts.empty:
            return None
        ts = ts.sort_values("dt")

        # Winsorize 1%–99% (membatasi outlier ekstrem)
        q1, q99 = ts["val"].quantile([0.01, 0.99])
        ts["val"] = ts["val"].clip(q1, q99)

        span = (ts["dt"].max() - ts["dt"].min())
        days = span.days + (span.seconds > 0)
        if days >= 365 * 2:
            rule = "W"      # weekly
        elif days >= 180:
            rule = "D"      # daily
        elif days >= 14:
            rule = "D"
        elif days >= 2:
            rule = "H"      # hourly
        else:
            rule = "15min"

        g = ts.set_index("dt").groupby(pd.Grouper(freq=rule))["val"].sum(min_count=1)
        g = g.interpolate(limit_direction="both").dropna()

        if len(g) < 3:
            return None

        # Downsample merata jika titik terlalu banyak
        if len(g) > max_points:
            idx = np.linspace(0, len(g) - 1, max_points).round().astype(int)
            g = g.iloc[idx]

        clean = g.reset_index().rename(columns={"val": value_col, "dt": date_col})
        # String tanggal agar sumbu-X tanpa jam
        clean["__date_str__"] = pd.to_datetime(clean[date_col]).dt.strftime("%Y-%m-%d")
        return clean

    # ======================================================================
    # HELPERS: scatter + smart charts (pakai time-series cleaned)
    # ======================================================================
    def _make_scatter(self, df: pd.DataFrame, xcol: str, ycol: str) -> Optional[Dict[str, Any]]:
        tmp = df[[xcol,ycol]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(tmp) < 10: return None
        if len(tmp) > 800: tmp = tmp.sample(800, random_state=42)
        pts = [{"x": float(xv), "y": float(yv)} for xv, yv in zip(tmp[xcol], tmp[ycol])]
        return {
            "type":"scatter",
            "title":f"Korelasi {xcol} vs {ycol}",
            "x_label":str(xcol),
            "y_label":str(ycol),
            "data": pts,
            "points": pts,
            "x_data": tmp[xcol].tolist(),
            "y_data": tmp[ycol].tolist(),
            "chart_purpose":"correlation",
            "series_name": f"{ycol}",
            "series": [{"name": f"{ycol}", "data": pts}],
        }

    def _smart_charts(self, df: pd.DataFrame, types: Dict[str, Any], num_cols: List[str])->Dict[str,Any]:
        charts: Dict[str, Any] = {}
        dt_cols  = [c for c,t in types.items() if t["detected_type"] == "datetime"]
        cat_cols = [c for c,t in types.items() if t["detected_type"] in ("categorical","text") and t.get("unique_count", 9999) <= 20]

        # 1) Time-series (rapi): line + cumulative area, X = tanggal (YYYY-MM-DD)
        if dt_cols and num_cols:
            d = dt_cols[0]
            for n in num_cols[:2]:
                clean = self._prepare_time_series(df, d, n, max_points=300)
                if clean is None or len(clean) <= 3:
                    continue
                x = clean["__date_str__"].tolist()
                y = clean[n].tolist()

                pts_line = [{"x": x[i], "y": _py(y[i])} for i in range(len(x))]
                charts[f"trend_{n}_over_time"] = {
                    "type": "line",
                    "title": f"Tren {n} vs Waktu",
                    "x_data": x,
                    "y_data": _py(y),
                    "x_label": d,
                    "y_label": n,
                    "chart_purpose": "time_series",
                    "x_axis_hint": {"is_datetime": True, "suggested_format": "%Y-%m-%d", "date_only": True},
                    "data": pts_line,
                    "series_name": str(n),
                    "series": [{"name": str(n), "data": pts_line}],
                }

                cum = clean[n].cumsum().tolist()
                pts_area = [{"x": x[i], "y": _py(cum[i])} for i in range(len(x))]
                charts[f"cumulative_{n}"] = {
                    "type": "area",
                    "title": f"Kumulatif {n}",
                    "x_data": x,
                    "y_data": _py(cum),
                    "x_label": d,
                    "y_label": f"Kumulatif {n}",
                    "chart_purpose": "cumulative",
                    "x_axis_hint": {"is_datetime": True, "suggested_format": "%Y-%m-%d", "date_only": True},
                    "data": pts_area,
                    "series_name": f"Kumulatif {n}",
                    "series": [{"name": f"Kumulatif {n}", "data": pts_area}],
                }

        # 2) Horizontal bar (ranking / distribusi kategori)
        if cat_cols:
            base = cat_cols[0]
            if num_cols:
                s = df.groupby(base)[num_cols[0]].sum().sort_values(ascending=False).head(10)
                xs = _py(s.values.tolist()); ys = s.index.astype(str).tolist()
                pts = [{"x": _py(v), "y": k} for k, v in zip(ys, xs)]
                charts[f"top_{base}_by_{num_cols[0]}"] = {
                    "type": "horizontal_bar",
                    "title": f"Top {base} by {num_cols[0]}",
                    "x_data": xs,
                    "y_data": ys,
                    "x_label": num_cols[0],
                    "y_label": base,
                    "chart_purpose": "ranking",
                    "data": pts,
                    "series_name": str(num_cols[0]),
                    "series": [{"name": str(num_cols[0]), "data": pts}],
                }
            if len(cat_cols) >= 2:
                other = cat_cols[1]
                ct = pd.crosstab(df[base].astype(str), df[other].astype(str)).head(10)
                # tetap pertahankan struktur lama, plus series_list agar gampang dipakai
                series_list = [{"name": str(col), "data": _py(ct[col].tolist())} for col in ct.columns]
                charts[f"stacked_{base}_by_{other}"] = {
                    "type": "stacked_bar",
                    "title": f"{base} × {other}",
                    "series": {str(col): _py(ct[col].tolist()) for col in ct.columns},
                    "series_list": series_list,
                    "categories": ct.index.astype(str).tolist(),
                    "chart_purpose": "composition",
                }

        # 3) Scatter untuk korelasi numerik
        if len(num_cols) >= 2:
            sc = self._make_scatter(df, num_cols[0], num_cols[1])
            if sc:
                charts[f"scatter_{num_cols[0]}_vs_{num_cols[1]}"] = sc

        # 4) Box plot untuk distribusi numerik
        for n in num_cols[:3]:
            s = df[n].dropna()
            if len(s) < 8:
                continue
            q1, q2, q3 = np.percentile(s, [25, 50, 75]); iqr = q3 - q1
            charts[f"box_{n}"] = {
                "type": "boxplot",
                "title": f"Sebaran {n}",
                "q1": _py(q1),
                "median": _py(q2),
                "q3": _py(q3),
                "whisker_low": _py(q1 - 1.5 * iqr),
                "whisker_high": _py(q3 + 1.5 * iqr),
                "chart_purpose": "distribution",
                "series_name": str(n),
            }
        return charts

    # ======================================================================
    # HELPERS: PDF
    # ======================================================================
    def _pdf_statistics(self, full_text: str, page_texts: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not full_text.strip():
            return {"pages": len(page_texts),"word_count":0,"char_count":0,
                    "paragraph_count":0,"sentence_count":0,"average_words_per_page":0}
        words = full_text.split()
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        sentences  = [s.strip() for s in re.split(r"[.!?]+", full_text) if s.strip()]
        lines = full_text.split("\n"); non_empty = [l for l in lines if l.strip()]
        pages_with_content = [p for p in page_texts if p.get("word_count",0) > 0]
        avg_wpp = (sum(p["word_count"] for p in pages_with_content)/len(pages_with_content)) if pages_with_content else 0
        return {"pages": len(page_texts),"word_count": len(words),"char_count": len(full_text),
                "char_count_no_spaces": len(full_text.replace(" ","")),
                "paragraph_count": len(paragraphs),"sentence_count": len(sentences),
                "line_count": len(lines),"non_empty_lines": len(non_empty),
                "average_words_per_page": round(avg_wpp,2),
                "average_chars_per_page": round(len(full_text)/len(page_texts),2) if page_texts else 0,
                "longest_paragraph": max((len(p) for p in paragraphs), default=0),
                "average_paragraph_length": round((sum(len(p) for p in paragraphs)/len(paragraphs)),2) if paragraphs else 0,
                "reading_time_minutes": round(len(words)/300,1), "processing_time_seconds":"0.0000"}

    def _pdf_ai_summary(self, text: str, gemini_model=None) -> str:
        if not gemini_model or not text.strip(): return "Summary not available"
        try:
            prompt = (
                "Ringkas dokumen berikut (Bahasa Indonesia) dengan format:\n"
                "1) Poin Kunci (3–5)\n2) Bukti & Angka\n3) Rekomendasi singkat (2–3)\n\n"
                f"Dokumen:\n{text}\n\nRingkasan:"
            )
            resp = gemini_model.generate_content(
                prompt, generation_config={"temperature":0.25,"top_p":0.95,"max_output_tokens":320}
            )
            return (getattr(resp, "text", None) or "").strip() or "Summary not available"
        except Exception as e:
            return f"Error generating summary: {str(e)}"
