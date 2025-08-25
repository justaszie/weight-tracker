export type DataSourceCTA = {
  srcName: DataSourceName;
  ctaText: string;
  icon: React.ComponentType;
}
export type DataSourceName = 'gfit' | 'mfp';

export function isDataSourceName(src?: string): src is DataSourceName {
  return (src && ['gfit', 'mfp'].includes(src)) ? true : false
}