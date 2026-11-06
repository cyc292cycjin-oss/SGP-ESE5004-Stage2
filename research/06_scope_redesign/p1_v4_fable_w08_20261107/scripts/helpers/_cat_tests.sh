cd /home/jin/wt_v4_fable/tests/research || exit 1
for f in test_v4_a2_fallback.py test_v4_anchor_iid.py test_v4_base_sdmx.py test_v4_biomass_potential.py test_v4_captive.py test_v4_industry_cache.py test_v4_products.py test_v4_profiles.py test_v4_registry.py test_v4_transport_accounts.py; do
  echo "##### $f"; cat -n "$f"
done
