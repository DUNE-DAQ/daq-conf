/************************************************************
 * create_config_plot.cpp
 *
 * JCF, May-7-2024
 *
 * Main file of create_config_plot used to generate GraphViz dot
 * files of DUNE DAQ configurations. The latter can
 * be used to generate graphs that visualize the database
 * patterns
 *
 * This is part of the DUNE DAQ Application Framework, copyright 2020.
 * Licensing/copyright details are in the COPYING file that you should have
 * received with this code.
 *
 *************************************************************/
#include "GraphBuilder.hpp"

#include "appmodel/appmodelIssues.hpp"
#include "logging/Logging.hpp"

#include <boost/program_options.hpp>

#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>

namespace bpo = boost::program_options;

int main(int argc, char* argv[])
{

  std::string oksfilename {""};
  std::string outputfilename {""};
  std::string object_uid {""};
  std::string sessionname {""};

  bpo::options_description options_description (
    "Allowed options", 128 );

  options_description.add_options()

  ( "help,h", "Provide help message" )

  ( "file,f", bpo::value<std::string> ( &oksfilename ), "OKS database file name" )

    ( "root-object,r", bpo::value<std::string>(&object_uid)->default_value(""), "OKS object UID of root vertex; must be session, segment or application")
    ( "session,s", bpo::value<std::string> ( &sessionname )->default_value(""),
    "Name of the session associated with the root object (only needed if >1 session in the database)" )
    ( "output,o", bpo::value<std::string> ( &outputfilename )->default_value("config.dot"),
    "Output DOT file which can be used as input to GraphViz" );

  bpo::variables_map args;

  auto display_help_message = [&options_description]()
  {
    TLOG() 
        << "create_config_plot : Generate dot graphs from database files"
        << std::endl
        << std::endl
        << "Usage: create_config_plot -f/--file <input OKS file> -r/--root-object <object UID for session, segment or application> (-s/--session <session containing root-object>) (-o/--output <output DOT file, default is config.dot>)"
        << std::endl
        << std::endl
        << options_description
        << std::endl;
  };

  try
  {
    bpo::store ( bpo::command_line_parser ( argc, argv ).options ( options_description ).run(),
                 args );
    bpo::notify ( args );
    
    if ( args.count ( "help" ) || ! args.count ( "file" ) )
    {
      display_help_message();
      return EXIT_FAILURE;
    }

    daqconf::GraphBuilder graphbuilder(oksfilename, sessionname);
    graphbuilder.construct_graph(object_uid);
    graphbuilder.write_graph(outputfilename);
    
  } catch (const bpo::error& e) {

    display_help_message();
    
    std::stringstream errmsgstr;
    errmsgstr << "Incorrect command line argument: " << e.what();
    ers::fatal(daqconf::GeneralGraphToolError(ERS_HERE, errmsgstr.str()));

  } catch (const dunedaq::appmodel::BadConf& exc) {
    std::stringstream errmsgstr;
    errmsgstr << "Caught BadConf exception: " << exc;
    ers::fatal(daqconf::GeneralGraphToolError(ERS_HERE, errmsgstr.str()));

  } catch(const daqconf::GeneralGraphToolError& e) {

    ers::fatal(e);

  }

  return 0;
}

