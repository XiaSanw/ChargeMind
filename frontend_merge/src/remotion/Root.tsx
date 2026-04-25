import { Composition } from 'remotion';
import ChargeMindVideo from './Video';

export const RemotionRoot = () => {
  return (
    <Composition
      id="ChargeMind"
      component={ChargeMindVideo}
      durationInFrames={1125}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{}}
    />
  );
};
