from pathlib import WindowsPath
import pytest
from sfrout.components.config import Config

correct_single_sfdc_wo_opt_params_input = {"cli_reports_list_path": "./tests/sample_files/correct_single_sfdc.csv", 
          "cli_report": "", 
          "cli_path": "", 
          "cli_threads": 0}

correct_single_sfdc_wo_opt_params_cli_path_input = {"cli_reports_list_path": "./tests/sample_files/correct_single_sfdc.csv", 
          "cli_report": "", 
          "cli_path": "C:\\CLI_Path", 
          "cli_threads": 0}

correct_single_sfdc_wo_opt_params_cli_report_input = {"cli_reports_list_path": "./tests/sample_files/correct_single_sfdc.csv", 
          "cli_report": "SFDC,correct_sfdc_report_with_optional_export_params_manual,11A1B000001abVa,C:\\Manual", 
          "cli_path": "",
          "cli_threads": 0}

correct_single_sfdc_wo_opt_params_cli_report_cli_path_input = {"cli_reports_list_path": "./tests/sample_files/correct_single_sfdc.csv", 
          "cli_report": "SFDC,correct_sfdc_report_with_optional_export_params_manual,11A1B000001abVa,C:\\Manual", 
          "cli_path": "C:\\CLI_Path",
          "cli_threads": 0}

correct_multi_sfdc_wo_opt_params_input = {"cli_reports_list_path": "./tests/sample_files/correct_multi_sfdc.csv", 
          "cli_report": "", 
          "cli_path": "", 
          "cli_threads": 0}

correct_single_sfdc_w_opt_params_input = {"cli_reports_list_path": "./tests/sample_files/correct_single_sfdc_opt_params.csv", 
          "cli_report": "", 
          "cli_path": "", 
          "cli_threads": 0}

correct_multi_sfdc_w_opt_params_input = {"cli_reports_list_path": "./tests/sample_files/correct_multi_sfdc_opt_params.csv", 
          "cli_report": "", 
          "cli_path": "", 
          "cli_threads": 0}


correct_single_sfdc_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_without_optional_export_params', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/')}]

correct_single_sfdc_cli_path_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_without_optional_export_params', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/CLI_Path')}]

correct_single_sfdc_cli_report_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_with_optional_export_params_manual', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/Manual'), 'params': ''}]

correct_single_sfdc_cli_report_cli_path_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_with_optional_export_params_manual', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/CLI_Path'), 'params': ''}]

correct_multi_sfdc_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_without_optional_export_params_win_path', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/')}, 
                                {'type': 'SFDC', 'name': 'correct_sfdc_report_without_optional_export_params_unix_path', 'id': '11A1B000001abVa', 'path': WindowsPath('/c')}]

correct_single_sfdc_w_opt_params_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_with_optional_export_params', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/'), 'params': '?export=&xf=localecsv&enc=UTF-8&scope=organization&pv1=4/1/2019&pv2=4/7/2019&isdtp=p1'}]

correct_multi_sfdc_w_opt_params_output = [{'type': 'SFDC', 'name': 'correct_sfdc_report_with_optional_export_params', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/'), 'params': '?export=&xf=localecsv&enc=UTF-8&scope=organization&pv1=4/1/2019&pv2=4/7/2019&isdtp=p1'}, 
                                          {'type': 'SFDC', 'name': 'correct_sfdc_report_with_optional_export_params', 'id': '11A1B000001abVa', 'path': WindowsPath('C:/'), 'params': '?export=&xf=localecsv&enc=UTF-8&scope=organization&pv1=4/1/2019&pv2=4/7/2019&isdtp=p1'}]

@pytest.fixture(scope='class', params=[correct_single_sfdc_wo_opt_params_input])
def config_obj_correct_single_wo_opt_params(request):
    return Config(**request.param)

@pytest.fixture(scope='class', params=[correct_single_sfdc_wo_opt_params_cli_path_input])
def config_obj_correct_single_cli_path_wo_opt_params(request):
    return Config(**request.param)

@pytest.fixture(scope='class', params=[correct_single_sfdc_wo_opt_params_cli_report_input])
def config_obj_correct_single_cli_report_wo_opt_params(request):
    return Config(**request.param)

@pytest.fixture(scope='class', params=[correct_single_sfdc_wo_opt_params_cli_report_cli_path_input])
def config_obj_correct_single_cli_report_cli_path_wo_opt_params(request):
    return Config(**request.param)

@pytest.fixture(scope='class', params=[correct_multi_sfdc_wo_opt_params_input])
def config_obj_correct_multi_wo_opt_params(request):
    return Config(**request.param)

@pytest.fixture(scope='class', params=[correct_single_sfdc_w_opt_params_input])
def config_obj_correct_single_w_opt_params(request):
    return Config(**request.param)

@pytest.fixture(scope='class', params=[correct_multi_sfdc_w_opt_params_input])
def config_obj_correct_multi_w_opt_params(request):
    return Config(**request.param)


@pytest.mark.usefixtures("config_obj_correct_single_wo_opt_params")
class TestInitConfigSingleWithoutOptParams:
    def test_init_config_single_without_opt_params(self, config_obj_correct_single_wo_opt_params):
        assert config_obj_correct_single_wo_opt_params.report_params_list == correct_single_sfdc_output
        assert len(config_obj_correct_single_wo_opt_params.report_params_list) == 1

@pytest.mark.usefixtures("config_obj_correct_single_cli_path_wo_opt_params")
class TestInitConfigSingleWithoutOptParamsCliPath:
    def test_init_config_single_without_opt_params_cli_path(self, config_obj_correct_single_cli_path_wo_opt_params):
        assert config_obj_correct_single_cli_path_wo_opt_params.report_params_list == correct_single_sfdc_cli_path_output
        assert len(config_obj_correct_single_cli_path_wo_opt_params.report_params_list) == 1

@pytest.mark.usefixtures("config_obj_correct_single_cli_report_wo_opt_params")
class TestInitConfigSingleWithoutOptParamsCliReport:
    def test_init_config_single_without_opt_params_cli_report(self, config_obj_correct_single_cli_report_wo_opt_params):
        assert config_obj_correct_single_cli_report_wo_opt_params.report_params_list == correct_single_sfdc_cli_report_output
        assert len(config_obj_correct_single_cli_report_wo_opt_params.report_params_list) == 1

@pytest.mark.usefixtures("config_obj_correct_single_cli_report_cli_path_wo_opt_params")
class TestInitConfigSingleWithoutOptParamsCliReportCliPath:
    def test_init_config_single_without_opt_params_cli_report_cli_path(self, config_obj_correct_single_cli_report_cli_path_wo_opt_params):
        assert config_obj_correct_single_cli_report_cli_path_wo_opt_params.report_params_list == correct_single_sfdc_cli_report_cli_path_output
        assert len(config_obj_correct_single_cli_report_cli_path_wo_opt_params.report_params_list) == 1

@pytest.mark.usefixtures("config_obj_correct_multi_wo_opt_params")
class TestInitConfigMultiWithoutOptParams:
    def test_init_config_multi_without_opt_params(self, config_obj_correct_multi_wo_opt_params):
        assert config_obj_correct_multi_wo_opt_params.report_params_list == correct_multi_sfdc_output
        assert len(config_obj_correct_multi_wo_opt_params.report_params_list) == 2

@pytest.mark.usefixtures("config_obj_correct_single_w_opt_params")
class TestInitConfigSingleWithOptParams:
    def test_init_config_single_with_opt_params(self, config_obj_correct_single_w_opt_params):
        assert config_obj_correct_single_w_opt_params.report_params_list == correct_single_sfdc_w_opt_params_output
        assert len(config_obj_correct_single_w_opt_params.report_params_list) == 1

@pytest.mark.usefixtures("config_obj_correct_multi_w_opt_params")
class TestInitConfigMultiWithOptParams:
    def test_init_config_multi_with_opt_params(self, config_obj_correct_multi_w_opt_params):
        assert config_obj_correct_multi_w_opt_params.report_params_list == correct_multi_sfdc_w_opt_params_output
        assert len(config_obj_correct_multi_w_opt_params.report_params_list) == 2
