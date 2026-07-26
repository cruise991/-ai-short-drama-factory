import { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Activity, Clock, AlertCircle, Plus, Image as ImageIcon } from 'lucide-react';
import CreateProjectModal from './CreateProjectModal';
import { useNavigate } from 'react-router-dom';

interface Project {
  id: number;
  project_slug: string;
  status: string;
  created_at: string;
  goal: string;
  format_type: string;
}

const ProjectList = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const navigate = useNavigate();

  const fetchProjects = async () => {
    try {
      const response = await axios.get('http://localhost:8008/api/projects/');
      setProjects(response.data);
    } catch (error) {
      console.error("Error fetching projects", error);
    }
  };

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Pending':
        return <span className="flex items-center text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded text-xs"><Clock className="w-3 h-3 mr-1" /> Pending</span>;
      case 'Running':
      case 'Drafting':
      case 'Draft_Completed':
      case 'Assets_Generated':
        return <span className="flex items-center text-blue-400 bg-blue-400/10 px-2 py-1 rounded text-xs"><Activity className="w-3 h-3 mr-1" /> {status.replace('_', ' ')}</span>;
      case 'Paused_By_Error':
        return <span className="flex items-center text-red-400 bg-red-400/10 px-2 py-1 rounded text-xs"><AlertCircle className="w-3 h-3 mr-1" /> Error</span>;
      case 'Completed':
        return <span className="flex items-center text-green-400 bg-green-400/10 px-2 py-1 rounded text-xs"><Play className="w-3 h-3 mr-1" /> Completed</span>;
      default:
        return <span className="flex items-center text-gray-400 bg-gray-400/10 px-2 py-1 rounded text-xs">{status}</span>;
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white mb-1">Production Queue</h2>
          <p className="text-gray-400 text-sm">Monitor and manage your AI short drama generation pipeline.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 border border-dashed border-gray-700 rounded-xl bg-gray-800/30">
          <p className="text-gray-400 mb-4">No projects in queue.</p>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map(project => (
            <div key={project.id} className="group bg-gray-800 border border-gray-700 rounded-xl p-5 hover:border-gray-500 transition-colors shadow-lg flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-white truncate pr-4" title={project.goal}>{project.goal}</h3>
                {getStatusBadge(project.status)}
              </div>
              <div className="text-sm text-gray-400 mb-4 flex-1">
                <p><span className="text-gray-500">Slug:</span> {project.project_slug}</p>
                <p><span className="text-gray-500">Format:</span> {project.format_type}</p>
              </div>
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-700">
                <span className="text-xs text-gray-500">
                  {new Date(project.created_at).toLocaleString()}
                </span>
                <button 
                  onClick={() => navigate(`/projects/${project.project_slug}/assets`)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-md transition-colors text-xs font-medium"
                >
                  <ImageIcon className="w-3.5 h-3.5 text-purple-400" />
                  Assets
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && (
        <CreateProjectModal 
          onClose={() => setIsModalOpen(false)} 
          onSuccess={() => {
            setIsModalOpen(false);
            fetchProjects();
          }} 
        />
      )}

    </div>
  );
};

export default ProjectList;
