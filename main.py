import os
from dotenv import load_dotenv
from multiprocessing import Pool, Manager

from components.connectors import SFDC_Connector
from components.internals import loading_cli_arguments
from components.report_excpetions import EnvFileNotPresent


if __name__ == '__main__':

    with Manager() as manager:
        
        print("")

        try:
            load_dotenv()
        except EnvFileNotPresent:
            print('.env file missing')

        abs_path, report_list, report_directory = loading_cli_arguments()

        final_report_path = abs_path + str(os.getenv("FINAL_REPORT_PATH"))
        domain = str(os.getenv("SFDC_DOMAIN"))

        connector = SFDC_Connector(domain=domain)
        connector.connection_check()

        reports = connector.load_reports_list(report_list, report_directory)

        result_reports = manager.list()

        pool = Pool(processes=len(reports))

        print("")
        print(f'Processing of {len(reports)} reports started')
        print(" ")
        print(f'0% [{len(reports) * " "}] 100%')
        print("    ", end='', flush=True)

        pool.starmap(connector.report_processing, [(report, result_reports) for report in reports])
        
        print(" ")
        print(" ")
        
        pool.close()
        pool.join()

        for report in result_reports:
            print(f'{report.file_name:<40} attempts: {report.attempt_count:>2}, size: {report.file_size:<5} Mb, time: {report.processing_time}')

        connector.final_report(result_reports, final_report_path)

        print(f'\nEnd of processing - {len(result_reports)} reports processed successfully')
