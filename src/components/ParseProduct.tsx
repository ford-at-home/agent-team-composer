import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowRight, FileText, Plus, X, Code, Eye } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import ReactMarkdown from 'react-markdown';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Form validation schema
const productSchema = z.object({
  title: z.string().min(1, 'Title is required').max(256),
  description: z.string().min(10, 'Description must be at least 10 characters').max(2048),
  domain: z.string().min(1, 'Domain is required'),
  targetUsers: z.array(z.string()).min(1, 'At least one target user is required'),
  techStack: z.array(z.string()).min(1, 'At least one technology is required'),
  features: z.array(z.string()).min(1, 'At least one feature is required'),
  complexity: z.enum(['simple', 'moderate', 'complex'])
});

type ProductFormData = z.infer<typeof productSchema>;

interface ParseProductProps {
  readmeContent?: string;
  initialData?: Partial<ProductFormData>;
  onNext: (data: ProductFormData) => void;
}

const ParseProduct = ({ readmeContent = '', initialData, onNext }: ParseProductProps) => {
  const [newTargetUser, setNewTargetUser] = useState('');
  const [newTech, setNewTech] = useState('');
  const [newFeature, setNewFeature] = useState('');
  const [previewMode, setPreviewMode] = useState<'raw' | 'preview'>('preview');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    getValues
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      title: initialData?.title || 'Untitled Project',
      description: initialData?.description || '',
      domain: initialData?.domain || 'general',
      targetUsers: initialData?.targetUsers || ['developers'],
      techStack: initialData?.techStack || [],
      features: initialData?.features || [],
      complexity: initialData?.complexity || 'moderate'
    }
  });

  const watchedValues = watch();

  // Domain options
  const domainOptions = [
    { value: 'e-commerce', label: 'E-commerce' },
    { value: 'social-media', label: 'Social Media' },
    { value: 'productivity', label: 'Productivity' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'finance', label: 'Finance' },
    { value: 'entertainment', label: 'Entertainment' },
    { value: 'devtools', label: 'Developer Tools' },
    { value: 'iot', label: 'IoT' },
    { value: 'general', label: 'General' }
  ];

  const addItem = (type: 'targetUsers' | 'techStack' | 'features', value: string) => {
    if (!value.trim()) return;
    
    const currentValues = getValues(type);
    if (!currentValues.includes(value)) {
      setValue(type, [...currentValues, value.trim()]);
    }
    
    // Clear input
    if (type === 'targetUsers') setNewTargetUser('');
    else if (type === 'techStack') setNewTech('');
    else if (type === 'features') setNewFeature('');
  };

  const removeItem = (type: 'targetUsers' | 'techStack' | 'features', index: number) => {
    const currentValues = getValues(type);
    setValue(type, currentValues.filter((_, i) => i !== index));
  };

  const onSubmit = (data: ProductFormData) => {
    onNext(data);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
          <CardTitle className="text-xl flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Parse Product
          </CardTitle>
          <CardDescription className="text-blue-100">
            Review and edit the detected project information
          </CardDescription>
        </CardHeader>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left Column - Form Fields */}
          <div className="space-y-4">
            {/* Title */}
            <Card>
              <CardContent className="pt-6">
                <Label htmlFor="title">Project Title</Label>
                <Input
                  id="title"
                  {...register('title')}
                  placeholder="My Awesome Project"
                  className="mt-2"
                />
                {errors.title && (
                  <p className="text-sm text-red-600 mt-1">{errors.title.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Description */}
            <Card>
              <CardContent className="pt-6">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  {...register('description')}
                  placeholder="A brief description of your project..."
                  rows={4}
                  className="mt-2"
                />
                {errors.description && (
                  <p className="text-sm text-red-600 mt-1">{errors.description.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Domain & Complexity */}
            <Card>
              <CardContent className="pt-6 space-y-4">
                <div>
                  <Label htmlFor="domain">Domain</Label>
                  <Select
                    value={watchedValues.domain}
                    onValueChange={(value) => setValue('domain', value)}
                  >
                    <SelectTrigger id="domain" className="mt-2">
                      <SelectValue placeholder="Select domain" />
                    </SelectTrigger>
                    <SelectContent>
                      {domainOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="complexity">Complexity</Label>
                  <Select
                    value={watchedValues.complexity}
                    onValueChange={(value: 'simple' | 'moderate' | 'complex') => 
                      setValue('complexity', value)
                    }
                  >
                    <SelectTrigger id="complexity" className="mt-2">
                      <SelectValue placeholder="Select complexity" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="simple">Simple</SelectItem>
                      <SelectItem value="moderate">Moderate</SelectItem>
                      <SelectItem value="complex">Complex</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Target Users */}
            <Card>
              <CardContent className="pt-6">
                <Label>Target Users</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    value={newTargetUser}
                    onChange={(e) => setNewTargetUser(e.target.value)}
                    placeholder="Add target user..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addItem('targetUsers', newTargetUser);
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    onClick={() => addItem('targetUsers', newTargetUser)}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {watchedValues.targetUsers.map((user, index) => (
                    <Badge key={index} variant="secondary" className="pr-1">
                      {user}
                      <button
                        type="button"
                        onClick={() => removeItem('targetUsers', index)}
                        className="ml-2 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                {errors.targetUsers && (
                  <p className="text-sm text-red-600 mt-1">{errors.targetUsers.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Tech Stack */}
            <Card>
              <CardContent className="pt-6">
                <Label>Tech Stack</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    value={newTech}
                    onChange={(e) => setNewTech(e.target.value)}
                    placeholder="Add technology..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addItem('techStack', newTech);
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    onClick={() => addItem('techStack', newTech)}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {watchedValues.techStack.map((tech, index) => (
                    <Badge key={index} variant="outline" className="pr-1">
                      {tech}
                      <button
                        type="button"
                        onClick={() => removeItem('techStack', index)}
                        className="ml-2 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                {errors.techStack && (
                  <p className="text-sm text-red-600 mt-1">{errors.techStack.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Features */}
            <Card>
              <CardContent className="pt-6">
                <Label>Key Features</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    value={newFeature}
                    onChange={(e) => setNewFeature(e.target.value)}
                    placeholder="Add feature..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addItem('features', newFeature);
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    onClick={() => addItem('features', newFeature)}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {watchedValues.features.map((feature, index) => (
                    <Badge key={index} className="pr-1">
                      {feature}
                      <button
                        type="button"
                        onClick={() => removeItem('features', index)}
                        className="ml-2 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                {errors.features && (
                  <p className="text-sm text-red-600 mt-1">{errors.features.message}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - README Preview */}
          <div className="lg:sticky lg:top-6">
            <Card className="h-full max-h-[80vh] overflow-hidden">
              <CardHeader>
                <CardTitle className="text-lg">README Content</CardTitle>
                <Tabs value={previewMode} onValueChange={(v) => setPreviewMode(v as 'raw' | 'preview')}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="preview" className="text-xs">
                      <Eye className="w-3 h-3 mr-1" />
                      Preview
                    </TabsTrigger>
                    <TabsTrigger value="raw" className="text-xs">
                      <Code className="w-3 h-3 mr-1" />
                      Raw
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </CardHeader>
              <CardContent className="overflow-y-auto max-h-[60vh]">
                <TabsContent value="preview" className="mt-0">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{readmeContent || '# No README content available'}</ReactMarkdown>
                  </div>
                </TabsContent>
                <TabsContent value="raw" className="mt-0">
                  <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto">
                    <code>{readmeContent || 'No README content available'}</code>
                  </pre>
                </TabsContent>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end">
          <Button 
            type="submit"
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          >
            Continue to Phase Generation
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ParseProduct;