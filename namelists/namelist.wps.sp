&share
 wrf_core = 'ARW',
 max_dom = 2,
 start_date = '2024-08-25_00:00:00', '2024-08-25_00:00:00', 
 end_date   = '2024-09-15_00:00:00', '2024-09-15_00:00:00', 
!opt_output_from_geogrid_path =  '/home/alejandro/projects/CR2/data',
 interval_seconds = 21600
/

&geogrid
 parent_id         =   1,    1,
 parent_grid_ratio =   1,    3,
 i_parent_start    =   1,   23,
 j_parent_start    =   1,   17,
 e_we              =  90,   75,
 e_sn              =  70,   75,
 geog_data_res = 'default', 'default', 
 dx = 9000,
 dy = 9000,
 map_proj = 'lambert', 
 ref_lat   = -23.00,
 ref_lon   = -45.50,
 truelat1  = -30.00,
 truelat2  = -60.00,
 stand_lon = -45.00,
 geog_data_path = '/home/alejandro/data/geog_v4/'
/

&ungrib
 out_format = 'WPS',
 prefix = 'FNL', 
/

&metgrid
 fg_name = 'FNL',
 io_form_metgrid = 2,
 opt_output_from_metgrid_path = '/home/alejandro/projects/CR2/data/',
 opt_metgrid_tbl_path         = './metgrid/',
/
